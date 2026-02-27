import logging
import sys
import os
from typing import Optional

logger = logging.getLogger(__name__)


# ── Path Setup ────────────────────────────────────────────────────────────────
# Since Phase1_Text, Phase2_Code, Phase3_Unified all live at the Turnitin/ root,
# we need to ensure the root is on sys.path so their imports resolve correctly.
# This dynamically adds the root regardless of where uvicorn is launched from.

def _ensure_root_on_path():
    # Phase4_Backend is at Turnitin/Phase4_Backend/
    # So root is two levels up from this file: Turnitin/
    current_file = os.path.abspath(__file__)                          # .../Phase4_Backend/app/services/engine_bridge.py
    phase4_dir   = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))  # .../Phase4_Backend/
    root_dir     = os.path.dirname(phase4_dir)                        # .../Turnitin/

    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        logger.info("Added root to sys.path: %s", root_dir)

_ensure_root_on_path()


# ── Engine Import ─────────────────────────────────────────────────────────────
# These imports will only succeed if the root path setup above worked correctly

try:
    from Phase3_Unified.engine.unified_analyzer import analyze_submission
    logger.info("Successfully imported Phase3 unified engine")
except ImportError as e:
    logger.critical(
        "Failed to import Phase3 engine. "
        "Make sure Phase1_Text, Phase2_Code, Phase3_Unified are at the project root. "
        "Error: %s", e
    )
    raise


# ── Bridge Function ───────────────────────────────────────────────────────────
def run_analysis(
    text1:          str,
    text2:          str,
    mode:           str,
    lang1_override: Optional[str] = None,
    lang2_override: Optional[str] = None,
) -> dict:
    """
    Thin wrapper around Phase3's analyze_submission().
    Called by the Celery worker — runs synchronously in the worker process.

    Args:
        text1:          Extracted text/code content of file 1
        text2:          Extracted text/code content of file 2
        mode:           'text' or 'code'
        lang1_override: Optional forced language for file 1
        lang2_override: Optional forced language for file 2

    Returns:
        dict with keys:
            mode, language, scores (dict), final_similarity, risk_level

    Raises:
        ValueError: if mode is invalid
        Exception:  any engine-level error (caught and logged by Celery task)
    """
    if not text1 or not text1.strip():
        raise ValueError("File 1 content is empty after extraction.")
    if not text2 or not text2.strip():
        raise ValueError("File 2 content is empty after extraction.")

    if mode not in ("text", "code"):
        raise ValueError(f"Invalid mode '{mode}'. Must be 'text' or 'code'.")

    logger.info(
        "Running analysis — mode=%s | lang_override=%s/%s | "
        "len(text1)=%d | len(text2)=%d",
        mode, lang1_override, lang2_override, len(text1), len(text2)
    )

    result = analyze_submission(
        input1         = text1,
        input2         = text2,
        mode           = mode,
        lang1_override = lang1_override,
        lang2_override = lang2_override,
    )

    logger.info(
        "Analysis complete — final_similarity=%.4f | risk=%s",
        result["final_similarity"], result["risk_level"]
    )

    return result