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
    from Phase2_Code.utils.language_detector import detect_language
    logger.info("Successfully imported Phase3 unified engine")
except ImportError as e:
    logger.critical(
        "Failed to import Phase3 engine. "
        "Make sure Phase1_Text, Phase2_Code, Phase3_Unified are at the project root. "
        "Error: %s", e
    )
    raise


# ── Bridge Function ───────────────────────────────────────────────────────────
def _ext_to_lang(ext: str) -> Optional[str]:
    """Maps file extension to language string."""
    if not ext:
        return None
    mapping = {
        ".py":   "python",
        ".java": "java",
        ".cpp":  "cpp",
        ".js":   "javascript",
    }
    return mapping.get(ext.lower())


def run_analysis(
    text1:          str,
    text2:          str,
    mode:           str,
    lang1_override: Optional[str] = None,
    lang2_override: Optional[str] = None,
    ext1:           Optional[str] = None,
    ext2:           Optional[str] = None,
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

    # Two-stage language resolution (code mode only)
    if mode == "code":
        lang1_from_ext = _ext_to_lang(ext1)
        lang2_from_ext = _ext_to_lang(ext2)

        # ── File 1 ──
        if lang1_override:
            final_lang1 = lang1_override.lower()
            logger.info("File1 language — user override: %s", final_lang1)
        else:
            content_lang1 = detect_language(text1)
            if content_lang1 is None:
                final_lang1 = lang1_from_ext
                logger.info("File1 language — content detector returned None, trusting extension: %s", final_lang1)
            elif content_lang1 == lang1_from_ext:
                final_lang1 = lang1_from_ext
                logger.info("File1 language — extension and content agree: %s", final_lang1)
            else:
                final_lang1 = lang1_from_ext
                logger.warning(
                    "File1 language — MISMATCH extension=%s content=%s, trusting extension",
                    lang1_from_ext, content_lang1
                )

        # ── File 2 ──
        if lang2_override:
            final_lang2 = lang2_override.lower()
            logger.info("File2 language — user override: %s", final_lang2)
        else:
            content_lang2 = detect_language(text2)
            if content_lang2 is None:
                final_lang2 = lang2_from_ext
                logger.info("File2 language — content detector returned None, trusting extension: %s", final_lang2)
            elif content_lang2 == lang2_from_ext:
                final_lang2 = lang2_from_ext
                logger.info("File2 language — extension and content agree: %s", final_lang2)
            else:
                final_lang2 = lang2_from_ext
                logger.warning(
                    "File2 language — MISMATCH extension=%s content=%s, trusting extension",
                    lang2_from_ext, content_lang2
                )

    else:
        final_lang1 = lang1_override
        final_lang2 = lang2_override

    logger.info(
        "Running analysis — mode=%s | lang=%s/%s | len(text1)=%d | len(text2)=%d",
        mode, final_lang1, final_lang2, len(text1), len(text2)
    )

    result = analyze_submission(
        input1         = text1,
        input2         = text2,
        mode           = mode,
        lang1_override = final_lang1,
        lang2_override = final_lang2,
    )

    logger.info(
        "Analysis complete — final_similarity=%.4f | risk=%s",
        result["final_similarity"], result["risk_level"]
    )

    return result