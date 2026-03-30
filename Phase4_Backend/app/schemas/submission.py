from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import datetime
from typing import Optional
from datetime import datetime
from app.models.submission import SubmissionMode, SubmissionStatus
from app.models.report import RiskLevel


# ── Scores breakdown (used inside ReportResponse) ────────────────────────────

class ScoresSchema(BaseModel):
    jaccard:   Optional[float] = None
    cosine:    Optional[float] = None
    lcs:       Optional[float] = None
    winnowing: Optional[float] = None
    ast:       Optional[float] = None


# ── Report (nested inside SubmissionDetailResponse) ──────────────────────────

class ReportSchema(BaseModel):
    id:                 int
    language:           Optional[str]
    scores:             ScoresSchema
    final_similarity:   float
    risk_level:         str  # Or RiskLevel if it's an Enum
    processing_time_ms: Optional[int]
    algorithm_version:  Optional[str]
    created_at:         datetime
    matched_blocks: Optional[list] = None

    @field_validator('matched_blocks', mode='before')
    @classmethod
    def coerce_matched_blocks(cls, v):
        if isinstance(v, dict):
            return [v] if v else None
        return v

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def map_flat_scores_to_nested(cls, data):
        # If 'data' is our SQLAlchemy model, it will have 'jaccard_score'
        if hasattr(data, 'jaccard_score'):
            # Reshape the flat SQLAlchemy object into the nested dictionary Pydantic expects
            return {
                "id": data.id,
                "language": data.language,
                "final_similarity": data.final_similarity,
                "risk_level": data.risk_level,
                "processing_time_ms": data.processing_time_ms,
                "algorithm_version": data.algorithm_version,
                "created_at": data.created_at,
                "matched_blocks": data.matched_blocks,
                "scores": {
                    "jaccard": data.jaccard_score,
                    "cosine": data.cosine_score,
                    "lcs": data.lcs_score,
                    "winnowing": data.winnowing_score,
                    "ast": data.ast_score,
                }
            }
        # If it's already a dict, just return it
        return data


# ── Submission List Item (lightweight, for history) ───────────────────────────

class SubmissionListItem(BaseModel):
    id:               int
    mode:             SubmissionMode
    file1_name:       str
    file2_name:       str
    status:           SubmissionStatus
    created_at:       datetime

    # Flattened report fields for quick display in history table
    final_similarity: Optional[float] = None
    risk_level:       Optional[RiskLevel] = None

    model_config = {"from_attributes": True}


# ── Submission Detail (full report included) ──────────────────────────────────

class SubmissionDetailResponse(BaseModel):
    id:                int
    mode:              SubmissionMode
    file1_name:        str
    file2_name:        str
    language_override: Optional[str]
    status:            SubmissionStatus
    error_message:     Optional[str]
    created_at:        datetime
    completed_at:      Optional[datetime]
    report:            Optional[ReportSchema] = None

    model_config = {"from_attributes": True}


# ── Upload Response (returned immediately after upload) ───────────────────────

class UploadResponse(BaseModel):
    submission_id: int
    status:        SubmissionStatus
    message:       str = "Files uploaded successfully. Analysis has been queued."


# ── Status Poll Response ──────────────────────────────────────────────────────

class StatusResponse(BaseModel):
    submission_id: int
    status:        SubmissionStatus
    message:       str


# ── History Response ──────────────────────────────────────────────────────────

class HistoryResponse(BaseModel):
    total:       int
    page:        int
    page_size:   int
    submissions: list[SubmissionListItem]


# ── Stats Response ────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_scans:        int
    average_similarity: float
    high_risk_count:    int
    most_used_mode:     str