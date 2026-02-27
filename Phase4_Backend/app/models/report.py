from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"


class Report(Base):
    __tablename__ = "reports"

    id              = Column(Integer, primary_key=True, index=True)
    submission_id   = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Detected / overridden language
    language        = Column(String(50), nullable=True)

    # Individual algorithm scores — nullable because not all apply to both modes
    jaccard_score   = Column(Float, nullable=True)     # text mode only
    cosine_score    = Column(Float, nullable=True)     # text mode only
    lcs_score       = Column(Float, nullable=True)     # both modes
    winnowing_score = Column(Float, nullable=True)     # code mode only
    ast_score       = Column(Float, nullable=True)     # code mode, same-language only

    # Final aggregated score and risk
    final_similarity = Column(Float, nullable=False)
    risk_level       = Column(SAEnum(RiskLevel), nullable=False)

    # Processing time in milliseconds
    processing_time_ms = Column(Integer, nullable=True)

    # Algorithm version tag — useful for reproducibility tracking
    algorithm_version  = Column(String(20), nullable=True, default="1.0.0")

    # Timestamps
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    submission      = relationship("Submission", back_populates="report")

    def __repr__(self) -> str:
        return f"<Report id={self.id} similarity={self.final_similarity} risk={self.risk_level}>"
