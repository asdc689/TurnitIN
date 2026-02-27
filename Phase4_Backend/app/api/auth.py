import logging
import urllib.parse
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, create_verification_token,
    create_password_reset_token, verify_email_token,
    verify_password_reset_token
)
from app.models.user import User, AuthProvider
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    UserResponse, MessageResponse, TokenRefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    UpdateProfileRequest, ChangePasswordRequest
)
from app.services.email_service import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Google OAuth URLs ─────────────────────────────────────────────────────────
GOOGLE_AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL   = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user with email and password."""

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    user = User(
        email           = payload.email,
        full_name       = payload.full_name,
        hashed_password = hash_password(payload.password),
        auth_provider   = AuthProvider.LOCAL,
        is_active       = True,
        is_verified     = False,    # email verification required
    )
    db.add(user)
    await db.flush()    # get user.id before commit

    # Send verification email
    verification_token = create_verification_token(user.email)
    send_verification_email(user.email, user.full_name or "User", verification_token)
    logger.info("New user registered: id=%d email=%s", user.id, user.email)

    return MessageResponse(
        message="Registration successful. Please check your email to verify your account."
    )


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Returns JWT access + refresh tokens."""

    result = await db.execute(select(User).where(User.email == payload.email))
    user   = result.scalar_one_or_none()

    # Single error message for both "not found" and "wrong password" (security best practice)
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    token_data    = {"sub": str(user.id)}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info("User logged in: id=%d", user.id)

    return TokenResponse(
        access_token  = access_token,
        refresh_token = refresh_token,
        user          = UserResponse.model_validate(user),
    )


# ── Refresh Token ─────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    decoded = decode_token(payload.refresh_token)

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = decoded.get("sub")
    result  = await db.execute(select(User).where(User.id == int(user_id)))
    user    = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    token_data    = {"sub": str(user.id)}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token  = access_token,
        refresh_token = refresh_token,
        user          = UserResponse.model_validate(user),
    )


# ── Get Current User ──────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


# ── Verify Email ──────────────────────────────────────────────────────────────
@router.get("/verify-email", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verifies a user's email address using the token sent to their inbox."""
    email = verify_email_token(token)

    result = await db.execute(select(User).where(User.email == email))
    user   = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_verified:
        return MessageResponse(message="Email already verified. You can log in.")

    user.is_verified = True
    logger.info("Email verified for user id=%d", user.id)

    return MessageResponse(message="Email verified successfully. You can now log in.")


# ── Forgot Password ───────────────────────────────────────────────────────────
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Sends a password reset email if the account exists.
    Always returns success to prevent email enumeration.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user   = result.scalar_one_or_none()

    # Always return success even if user doesn't exist (security best practice)
    if user and user.auth_provider.value == "LOCAL":
        reset_token = create_password_reset_token(user.email)
        send_password_reset_email(user.email, user.full_name or "User", reset_token)
        logger.info("Password reset email sent to %s", user.email)

    return MessageResponse(
        message="If an account with that email exists, a password reset link has been sent."
    )


# ── Reset Password ────────────────────────────────────────────────────────────
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Resets the user's password using a valid reset token."""
    email = verify_password_reset_token(payload.token)

    result = await db.execute(select(User).where(User.email == email))
    user   = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.auth_provider.value != "LOCAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google login. Password reset is not available."
        )

    user.hashed_password = hash_password(payload.new_password)
    logger.info("Password reset for user id=%d", user.id)

    return MessageResponse(message="Password reset successful. You can now log in.")


# ── Update Profile ────────────────────────────────────────────────────────────
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates the current user's full name."""
    current_user.full_name = payload.full_name
    await db.commit()
    await db.refresh(current_user)
    logger.info("Profile updated for user id=%d", current_user.id)
    return UserResponse.model_validate(current_user)


# ── Change Password ───────────────────────────────────────────────────────────
@router.put("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Changes the current user's password after verifying the current one."""
    if current_user.auth_provider.value != "LOCAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is not available for Google accounts."
        )

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )

    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    logger.info("Password changed for user id=%d", current_user.id)

    return MessageResponse(message="Password changed successfully.")


# ── Google OAuth — Initiate ───────────────────────────────────────────────────
@router.get("/google")
async def google_login():
    """Redirects the user to Google's OAuth2 consent screen."""
    params = {
        "client_id":     settings.GOOGLE_CLIENT_ID,
        "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{query_string}")


# ── Google OAuth — Callback ───────────────────────────────────────────────────
@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """
    Google redirects here after user consent.
    Exchanges the auth code for tokens, fetches user info,
    creates or logs in the user, redirects to frontend with JWT tokens.
    """
    async with httpx.AsyncClient() as client:
        # 1. Exchange auth code for Google access token
        token_response = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri":  settings.GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange Google authorization code"
            )

        google_tokens = token_response.json()

        # 2. Fetch user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_tokens['access_token']}"}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user info"
            )

        google_user = userinfo_response.json()

    google_id = google_user.get("sub")
    email     = google_user.get("email")
    full_name = google_user.get("name")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account has no email"
        )

    # 3. Find existing user or create new one
    result = await db.execute(select(User).where(User.email == email))
    user   = result.scalar_one_or_none()

    if not user:
        # New user via Google
        user = User(
            email         = email,
            full_name     = full_name,
            google_id     = google_id,
            auth_provider = AuthProvider.GOOGLE,
            is_active     = True,
            is_verified   = True,   # Google already verified the email
        )
        db.add(user)
        await db.flush()
        logger.info("New user via Google OAuth: id=%d email=%s", user.id, email)
    else:
        # Existing user — update Google ID if not set
        if not user.google_id:
            user.google_id     = google_id
            user.auth_provider = AuthProvider.GOOGLE
            user.is_verified   = True

    user.last_login = datetime.now(timezone.utc)

    token_data    = {"sub": str(user.id)}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Safely extract the frontend URL from settings
    try:
        if isinstance(settings.ALLOWED_ORIGINS, list):
            frontend_url = str(settings.ALLOWED_ORIGINS[0])
        else:
            frontend_url = str(settings.ALLOWED_ORIGINS).split(",")[0]
    except (IndexError, AttributeError):
        frontend_url = "http://localhost:3000"

    # Redirect browser back to frontend with tokens in query params
    params = urllib.parse.urlencode({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "name": user.full_name
    })

    return RedirectResponse(url=f"{frontend_url}/oauth/callback?{params}")