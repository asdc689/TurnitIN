from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class UserPlan(str, enum.Enum):
    FREE = "free"
    PRO  = "pro"


class AuthProvider(str, enum.Enum):
    LOCAL  = "local"    # email + password
    GOOGLE = "google"   # Google OAuth


class User(Base):
    __tablename__ = "users"

    id                = Column(Integer, primary_key=True, index=True)
    email             = Column(String(255), unique=True, index=True, nullable=False)
    full_name         = Column(String(255), nullable=True)
    hashed_password   = Column(String(255), nullable=True)   # nullable for OAuth users

    # Auth provider — LOCAL or GOOGLE
    auth_provider     = Column(SAEnum(AuthProvider), default=AuthProvider.LOCAL, nullable=False)
    google_id         = Column(String(255), unique=True, nullable=True)   # Google OAuth sub

    # Account state
    is_active         = Column(Boolean, default=True,  nullable=False)
    is_verified       = Column(Boolean, default=False, nullable=False)

    # Plan
    plan              = Column(SAEnum(UserPlan), default=UserPlan.FREE, nullable=False)

    # Timestamps
    created_at        = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login        = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    submissions       = relationship("Submission", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} plan={self.plan}>"
