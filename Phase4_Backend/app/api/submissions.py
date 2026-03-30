import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.database import get_db
from app.core.security import get_current_verified_user
from app.core.config import settings
from app.models.user import User, UserPlan
from app.models.submission import Submission, SubmissionMode, SubmissionStatus
from app.models.report import Report
from app.schemas.submission import (
    UploadResponse, StatusResponse, SubmissionDetailResponse,
    HistoryResponse, SubmissionListItem
)
from app.services.file_service import validate_file, upload_file_to_storage, delete_file_from_storage
from app.workers.tasks import run_plagiarism_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/submissions", tags=["Submissions"])


# ── Helper: check daily quota ─────────────────────────────────────────────────
async def check_daily_quota(user: User, db: AsyncSession):
    """
    Free plan users are limited to MAX_SUBMISSIONS_PER_DAY_FREE submissions/day.
    Pro plan users have no limit.
    """
    if user.plan == UserPlan.PRO:
        return

    from sqlalchemy import func, cast, Date
    from datetime import date

    today_count_result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.user_id == user.id)
        .where(func.cast(Submission.created_at, Date) == date.today())
    )
    today_count = today_count_result.scalar_one()

    if today_count >= settings.MAX_SUBMISSIONS_PER_DAY_FREE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Free plan limit reached: {settings.MAX_SUBMISSIONS_PER_DAY_FREE} "
                f"submissions per day. Upgrade to Pro for unlimited access."
            )
        )


# ── Upload ────────────────────────────────────────────────────────────────────
@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_submission(
    file1:         UploadFile      = File(..., description="First file for comparison"),
    file2:         UploadFile      = File(..., description="Second file for comparison"),
    mode:          str             = Form(..., description="'text' or 'code'"),
    lang_override: Optional[str]   = Form(None, description="Optional: force language ('python', 'java', 'cpp')"),
    db:            AsyncSession    = Depends(get_db),
    current_user:  User            = Depends(get_current_verified_user),
):
    """
    Upload two files for plagiarism analysis.

    - Validates file types and sizes
    - Uploads to MinIO/S3 storage
    - Creates a Submission record in DB
    - Dispatches a Celery background task
    - Returns submission_id immediately (non-blocking)

    Poll `/submissions/{id}/status` to track progress.
    """
    # Validate mode
    if mode not in ("text", "code"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mode must be 'text' or 'code'"
        )

    # Check daily quota
    await check_daily_quota(current_user, db)

    # Validate file types
    ext1 = validate_file(file1, mode)
    ext2 = validate_file(file2, mode)

    # Upload both files to storage
    file1_path, _ = await upload_file_to_storage(file1, current_user.id)
    file2_path, _ = await upload_file_to_storage(file2, current_user.id)

    # Create submission record
    submission = Submission(
        user_id           = current_user.id,
        mode              = SubmissionMode(mode),
        file1_name        = file1.filename,
        file2_name        = file2.filename,
        file1_path        = file1_path,
        file2_path        = file2_path,
        language_override = lang_override,
        status            = SubmissionStatus.PENDING,
    )
    db.add(submission)
    await db.flush()    # get submission.id

    # Dispatch Celery task
    task = run_plagiarism_analysis.delay(
        submission_id  = submission.id,
        file1_path     = file1_path,
        file2_path     = file2_path,
        mode           = mode,
        lang1_override = lang_override,
        lang2_override = lang_override,
        ext1           = ext1,
        ext2           = ext2,
    )

    # Store Celery task ID for tracking
    submission.celery_task_id = task.id
    await db.flush()

    logger.info(
        "Submission created: id=%d user=%d mode=%s task_id=%s",
        submission.id, current_user.id, mode, task.id
    )

    return UploadResponse(submission_id=submission.id, status=SubmissionStatus.PENDING)


# ── Status Poll ───────────────────────────────────────────────────────────────
@router.get("/{submission_id}/status", response_model=StatusResponse)
async def get_submission_status(
    submission_id: int,
    db:            AsyncSession = Depends(get_db),
    current_user:  User         = Depends(get_current_verified_user),
):
    """
    Poll the status of a submission.
    Returns: pending | processing | completed | failed
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .where(Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    status_messages = {
        SubmissionStatus.PENDING:    "Your submission is queued for analysis.",
        SubmissionStatus.PROCESSING: "Analysis is in progress. This may take a moment.",
        SubmissionStatus.COMPLETED:  "Analysis complete. Your report is ready.",
        SubmissionStatus.FAILED:     f"Analysis failed: {submission.error_message or 'Unknown error'}",
    }

    return StatusResponse(
        submission_id = submission.id,
        status        = submission.status,
        message       = status_messages[submission.status],
    )


# ── Get Full Report ───────────────────────────────────────────────────────────
@router.get("/{submission_id}/report", response_model=SubmissionDetailResponse)
async def get_submission_report(
    submission_id: int,
    db:            AsyncSession = Depends(get_db),
    current_user:  User         = Depends(get_current_verified_user),
):
    """
    Returns the full submission details including the analysis report.
    Only available once status is 'completed'.
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .where(Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Always return the submission — frontend handles all status states
    return SubmissionDetailResponse.model_validate(submission)


# ── Get File Contents ─────────────────────────────────────────────────────────
@router.get("/{submission_id}/files")
async def get_submission_files(
    submission_id: int,
    db:            AsyncSession = Depends(get_db),
    current_user:  User         = Depends(get_current_verified_user),
):
    """
    Returns the raw text content of both uploaded files.
    Used by the frontend for side-by-side code comparison view.
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .where(Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    from app.services.file_service import download_file_from_storage, extract_text
    import os

    try:
        file1_bytes = download_file_from_storage(submission.file1_path)
        file2_bytes = download_file_from_storage(submission.file2_path)

        ext1 = os.path.splitext(submission.file1_name)[1].lower()
        ext2 = os.path.splitext(submission.file2_name)[1].lower()

        content1 = extract_text(file1_bytes, ext1)
        content2 = extract_text(file2_bytes, ext2)

    except Exception as e:
        logger.error("Failed to fetch file contents for submission %d: %s", submission_id, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not retrieve file contents from storage."
        )

    return {
        "file1": {
            "name":    submission.file1_name,
            "content": content1,
        },
        "file2": {
            "name":    submission.file2_name,
            "content": content2,
        }
    }


# ── History ───────────────────────────────────────────────────────────────────
@router.get("/history", response_model=HistoryResponse)
async def get_submission_history(
    page:         int           = Query(default=1, ge=1),
    page_size:    int           = Query(default=8, ge=1, le=50),
    mode:         Optional[str] = Query(default=None, description="Filter by 'text' or 'code'"),
    risk:         Optional[str] = Query(default=None, description="Filter by risk: 'LOW', 'MEDIUM', 'HIGH'"),
    sort:         str           = Query(default="desc", pattern="^(asc|desc)$"),
    db:           AsyncSession  = Depends(get_db),
    current_user: User          = Depends(get_current_verified_user),
):
    from sqlalchemy import asc
    
    # Build dynamic conditions
    conditions = [Submission.user_id == current_user.id]

    if mode in ("text", "code"):
        conditions.append(Submission.mode == SubmissionMode(mode))

    if risk in ("LOW", "MEDIUM", "HIGH"):
        from app.models.report import RiskLevel
        conditions.append(
            Report.risk_level == RiskLevel(risk)
        )

    # Base query
    base_query = select(Submission)
    
    if risk in ("LOW", "MEDIUM", "HIGH"):
        base_query = base_query.join(Report, Report.submission_id == Submission.id)

    base_query = base_query.where(*conditions)

    # Total count with filters applied
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    # Sorting
    order_clause = desc(Submission.created_at) if sort == "desc" else asc(Submission.created_at)

    # Paginated fetch
    result = await db.execute(
        base_query
        .order_by(order_clause)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    submissions = result.scalars().all()

    items = []
    for sub in submissions:
        item = SubmissionListItem(
            id               = sub.id,
            mode             = sub.mode,
            file1_name       = sub.file1_name,
            file2_name       = sub.file2_name,
            status           = sub.status,
            created_at       = sub.created_at,
            final_similarity = sub.report.final_similarity if sub.report else None,
            risk_level       = sub.report.risk_level       if sub.report else None,
        )
        items.append(item)

    return HistoryResponse(
        total       = total,
        page        = page,
        page_size   = page_size,
        submissions = items,
    )


# ── Stats ─────────────────────────────────────────────────────────────────────
@router.get("/stats")
async def get_submission_stats(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_verified_user),
):
    """
    Returns aggregated stats for the current user's submissions.
    Used by the Dashboard stats cards.
    """
    from sqlalchemy import func, case
    from app.models.report import RiskLevel

    # Total scans
    total_result = await db.execute(
        select(func.count(Submission.id))
        .where(Submission.user_id == current_user.id)
    )
    total_scans = total_result.scalar_one()

    # Average similarity + high risk count
    report_result = await db.execute(
        select(
            func.avg(Report.final_similarity),
            func.count(
                case((Report.risk_level == RiskLevel.HIGH, 1))
            )
        )
        .join(Submission, Submission.id == Report.submission_id)
        .where(Submission.user_id == current_user.id)
    )
    row = report_result.one()
    average_similarity = round(float(row[0]), 4) if row[0] is not None else 0.0
    high_risk_count    = row[1] or 0

    # Most used mode
    mode_result = await db.execute(
        select(Submission.mode, func.count(Submission.id).label("count"))
        .where(Submission.user_id == current_user.id)
        .group_by(Submission.mode)
        .order_by(desc("count"))
        .limit(1)
    )
    mode_row       = mode_result.first()
    most_used_mode = mode_row[0].value if mode_row else "—"

    return {
        "total_scans":        total_scans,
        "average_similarity": average_similarity,
        "high_risk_count":    high_risk_count,
        "most_used_mode":     most_used_mode,
    }


# ── History Graph ─────────────────────────────────────────────────────────────
@router.get("/history-graph")
async def get_history_graph(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_verified_user),
):
    """
    Returns data for the Dashboard similarity history graph.
    - Line chart: similarity score per submission over time
    - Pie/bar chart: risk level distribution
    """
    from app.models.report import RiskLevel

    # Line chart data — last 20 completed submissions ordered by date
    line_result = await db.execute(
        select(
            Submission.id,
            Submission.created_at,
            Submission.mode,
            Report.final_similarity,
            Report.risk_level,
        )
        .join(Report, Report.submission_id == Submission.id)
        .where(Submission.user_id == current_user.id)
        .where(Submission.status == SubmissionStatus.COMPLETED)
        .order_by(Submission.created_at.asc())
        .limit(20)
    )
    rows = line_result.all()

    timeline = [
        {
            "id":         row.id,
            "date":       row.created_at.strftime("%b %d"),
            "similarity": round(row.final_similarity * 100, 1),
            "mode":       row.mode.value,
            "risk":       row.risk_level.value,
        }
        for row in rows
    ]

    # Risk distribution
    risk_result = await db.execute(
        select(Report.risk_level, func.count(Report.id).label("count"))
        .join(Submission, Submission.id == Report.submission_id)
        .where(Submission.user_id == current_user.id)
        .group_by(Report.risk_level)
    )
    risk_rows = risk_result.all()

    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for row in risk_rows:
        risk_distribution[row.risk_level.value] = row.count

    return {
        "timeline":          timeline,
        "risk_distribution": risk_distribution,
    }


# ── Delete ────────────────────────────────────────────────────────────────────
@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: int,
    db:            AsyncSession = Depends(get_db),
    current_user:  User         = Depends(get_current_verified_user),
):
    """
    Deletes a submission, its report, and its files from storage.
    """
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id)
        .where(Submission.user_id == current_user.id)
    )
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Delete files from storage
    delete_file_from_storage(submission.file1_path)
    delete_file_from_storage(submission.file2_path)

    # Delete DB record (cascade deletes the report too)
    await db.delete(submission)

    logger.info("Submission deleted: id=%d user=%d", submission_id, current_user.id)