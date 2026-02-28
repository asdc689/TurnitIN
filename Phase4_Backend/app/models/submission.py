from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SubmissionMode(str, enum.Enum):
    TEXT = "text"
    CODE = "code"


class SubmissionStatus(str, enum.Enum):
    PENDING    = "pending"      # just uploaded, not yet queued
    PROCESSING = "processing"   # Celery worker picked it up
    COMPLETED  = "completed"    # analysis finished successfully
    FAILED     = "failed"       # analysis threw an exception


class Submission(Base):
    __tablename__ = "submissions"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Mode — text or code
    mode             = Column(SAEnum(SubmissionMode), nullable=False)

    # File metadata (paths stored in MinIO/S3, not local disk)
    file1_name       = Column(String(255), nullable=False)
    file2_name       = Column(String(255), nullable=False)
    file1_path       = Column(String(512), nullable=False)   # storage object key
    file2_path       = Column(String(512), nullable=False)

    # Optional manual language override (for code mode)
    # If None, auto-detection was used
    language_override = Column(String(20), nullable=True)

    # Job tracking
    celery_task_id   = Column(String(255), nullable=True)
    status           = Column(SAEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    error_message    = Column(String(1024), nullable=True)   # populated on FAILED

    # Timestamps
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at     = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user    = relationship("User", back_populates="submissions")
    report  = relationship("Report", back_populates="submission", uselist=False, lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Submission id={self.id} mode={self.mode} status={self.status}>"
