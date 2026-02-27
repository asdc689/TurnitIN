import logging
import time
from datetime import datetime, timezone
from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Celery App ────────────────────────────────────────────────────────────────
celery_app = Celery(
    "turnitin_worker",
    broker  = settings.CELERY_BROKER_URL,
    backend = settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer        = "json",
    result_serializer      = "json",
    accept_content         = ["json"],
    timezone               = "UTC",
    enable_utc             = True,
    task_track_started     = True,
    task_acks_late         = True,      # only ack after task completes (safer)
    worker_prefetch_multiplier = 1,     # one task per worker at a time (CPU heavy)
    result_expires         = 86400,     # results expire after 24 hours
)


# ── Sync DB setup for Celery worker ──────────────────────────────────────────
# Celery runs synchronously, so we use psycopg2 (sync) not asyncpg
def get_sync_session():
    engine  = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


# ── Main Analysis Task ────────────────────────────────────────────────────────
@celery_app.task(
    bind                = True,
    name                = "tasks.run_plagiarism_analysis",
    max_retries         = 2,
    default_retry_delay = 10,     # seconds between retries
    soft_time_limit     = 300,    # 5 min soft limit (raises exception)
    time_limit          = 360,    # 6 min hard kill
)
def run_plagiarism_analysis(
    self,
    submission_id:  int,
    file1_path:     str,
    file2_path:     str,
    mode:           str,
    lang1_override: str = None,
    lang2_override: str = None,
):
    """
    Celery task: downloads files from storage, runs the plagiarism engine,
    saves the report to DB, updates submission status.

    This task is dispatched by the submission API endpoint and runs
    completely asynchronously in the Celery worker process.
    """
    from app.models.submission import Submission, SubmissionStatus
    from app.models.report import Report, RiskLevel
    from app.services.file_service import download_file_from_storage, extract_text
    from app.services.engine_bridge import run_analysis
    import os

    db = get_sync_session()
    start_time = time.time()

    try:
        # ── 1. Mark as PROCESSING ─────────────────────────────────────────────
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error("Submission %d not found in DB", submission_id)
            return

        submission.status = SubmissionStatus.PROCESSING
        db.commit()
        logger.info("Task started for submission_id=%d", submission_id)

        # ── 2. Download files from storage ────────────────────────────────────
        file1_bytes = download_file_from_storage(file1_path)
        file2_bytes = download_file_from_storage(file2_path)

        # ── 3. Extract text ───────────────────────────────────────────────────
        ext1  = os.path.splitext(submission.file1_name)[1].lower()
        ext2  = os.path.splitext(submission.file2_name)[1].lower()
        text1 = extract_text(file1_bytes, ext1)
        text2 = extract_text(file2_bytes, ext2)

        # ── 4. Run engine ─────────────────────────────────────────────────────
        result = run_analysis(
            text1          = text1,
            text2          = text2,
            mode           = mode,
            lang1_override = lang1_override,
            lang2_override = lang2_override,
        )

        # ── 5. Calculate processing time ──────────────────────────────────────
        processing_ms = int((time.time() - start_time) * 1000)

        # ── 6. Save report ────────────────────────────────────────────────────
        scores = result.get("scores", {})
        report = Report(
            submission_id      = submission_id,
            language           = result.get("language"),
            jaccard_score      = scores.get("jaccard"),
            cosine_score       = scores.get("cosine"),
            lcs_score          = scores.get("lcs"),
            winnowing_score    = scores.get("winnowing"),
            ast_score          = scores.get("ast"),
            final_similarity   = result["final_similarity"],
            risk_level         = result["risk_level"],
            processing_time_ms = processing_ms,
            algorithm_version  = "1.0.0",
        )
        db.add(report)

        # ── 7. Mark submission COMPLETED ──────────────────────────────────────
        submission.status       = SubmissionStatus.COMPLETED
        submission.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Analysis complete for submission_id=%d | "
            "similarity=%.4f | risk=%s | time=%dms",
            submission_id, result["final_similarity"],
            result["risk_level"], processing_ms
        )

    except Exception as exc:
        db.rollback()
        logger.exception("Task failed for submission_id=%d: %s", submission_id, exc)

        # Mark submission as FAILED
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status        = SubmissionStatus.FAILED
                submission.error_message = str(exc)[:1024]
                db.commit()
        except Exception as db_exc:
            logger.error("Failed to update submission status to FAILED: %s", db_exc)

        # Retry if we haven't exceeded max_retries
        raise self.retry(exc=exc)

    finally:
        db.close()