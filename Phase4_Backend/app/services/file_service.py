import io
import uuid
import logging
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Allowed file types ────────────────────────────────────────────────────────
ALLOWED_TEXT_EXTENSIONS = {".txt", ".pdf", ".docx"}
ALLOWED_CODE_EXTENSIONS = {".py", ".java", ".cpp", ".c", ".js", ".ts", ".cs", ".go", ".rb"}
ALL_ALLOWED_EXTENSIONS  = ALLOWED_TEXT_EXTENSIONS | ALLOWED_CODE_EXTENSIONS


# ── S3 / MinIO Client ─────────────────────────────────────────────────────────
def get_storage_client():
    """
    Returns a boto3 S3 client configured for either MinIO (local)
    or AWS S3 (production) based on settings.
    """
    kwargs = dict(
        aws_access_key_id     = settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key = settings.STORAGE_SECRET_KEY,
        use_ssl               = settings.STORAGE_USE_SSL,
    )
    # If STORAGE_ENDPOINT is set, we're using MinIO
    if settings.STORAGE_ENDPOINT:
        kwargs["endpoint_url"] = settings.STORAGE_ENDPOINT

    return boto3.client("s3", **kwargs)


def ensure_bucket_exists():
    """Creates the storage bucket if it doesn't exist (MinIO only)."""
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=settings.STORAGE_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.STORAGE_BUCKET_NAME)
        logger.info("Created storage bucket: %s", settings.STORAGE_BUCKET_NAME)


# ── Validation ────────────────────────────────────────────────────────────────
def validate_file(file: UploadFile, mode: str) -> str:
    """
    Validates file extension and size.
    Returns the file extension on success.
    Raises HTTPException on failure.
    """
    import os
    ext = os.path.splitext(file.filename or "")[1].lower()

    if mode == "text" and ext not in ALLOWED_TEXT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Text mode only supports: {', '.join(ALLOWED_TEXT_EXTENSIONS)}"
        )

    if mode == "code" and ext not in ALLOWED_CODE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Code mode only supports: {', '.join(ALLOWED_CODE_EXTENSIONS)}"
        )

    return ext


# ── Text Extraction ───────────────────────────────────────────────────────────
def extract_text_from_pdf(content: bytes) -> str:
    """Extracts plain text from a PDF file's bytes."""
    try:
        reader = PdfReader(io.BytesIO(content))
        text   = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from the PDF."
        )


def extract_text_from_docx(content: bytes) -> str:
    """Extracts plain text from a DOCX file's bytes."""
    try:
        doc  = Document(io.BytesIO(content))
        text = "\n".join(para.text for para in doc.paragraphs)
        return text.strip()
    except Exception as e:
        logger.error("DOCX extraction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract text from the DOCX file."
        )


def extract_text(content: bytes, extension: str) -> str:
    """
    Dispatcher: extracts raw text from uploaded file bytes
    based on file extension.
    """
    if extension == ".pdf":
        return extract_text_from_pdf(content)
    elif extension == ".docx":
        return extract_text_from_docx(content)
    else:
        # .txt or any code file — decode as UTF-8
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")


# ── Upload to Storage ─────────────────────────────────────────────────────────
async def upload_file_to_storage(file: UploadFile, user_id: int) -> tuple[str, bytes]:
    """
    Reads the uploaded file, validates size, uploads to MinIO/S3.

    Returns:
        (object_key, file_content_bytes)
        object_key is the path inside the bucket — used to retrieve later.
    """
    content = await file.read()

    # Size check
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Generate a unique object key: users/{user_id}/{uuid}_{original_filename}
    unique_id  = uuid.uuid4().hex
    object_key = f"users/{user_id}/{unique_id}_{file.filename}"

    try:
        client = get_storage_client()
        client.put_object(
            Bucket      = settings.STORAGE_BUCKET_NAME,
            Key         = object_key,
            Body        = content,
            ContentType = file.content_type or "application/octet-stream",
        )
        logger.info("Uploaded file to storage: %s", object_key)
    except ClientError as e:
        logger.error("Storage upload failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="File storage service is unavailable. Please try again later."
        )

    return object_key, content


def download_file_from_storage(object_key: str) -> bytes:
    """
    Downloads a file from MinIO/S3 by its object key.
    Used by the Celery worker to retrieve files for analysis.
    """
    try:
        client   = get_storage_client()
        response = client.get_object(Bucket=settings.STORAGE_BUCKET_NAME, Key=object_key)
        return response["Body"].read()
    except ClientError as e:
        logger.error("Storage download failed for key=%s: %s", object_key, e)
        raise RuntimeError(f"Could not retrieve file from storage: {object_key}")


def delete_file_from_storage(object_key: str) -> None:
    """Deletes a file from MinIO/S3. Called when user deletes a submission."""
    try:
        client = get_storage_client()
        client.delete_object(Bucket=settings.STORAGE_BUCKET_NAME, Key=object_key)
        logger.info("Deleted file from storage: %s", object_key)
    except ClientError as e:
        logger.warning("Storage delete failed for key=%s: %s", object_key, e)