import logging

from Phase1_Text.engine.text_similarity import compare_texts
from Phase2_Code.utils.language_detector import detect_language
from Phase2_Code.engine.code_similarity_engine import compare_code
from Phase3_Unified.engine.risk_classifier import classify_risk

logger = logging.getLogger(__name__)


def analyze_submission(
    input1: str,
    input2: str,
    mode: str,
    lang1_override: str = None,
    lang2_override: str = None
) -> dict:
    """
    Unified entry point for plagiarism analysis.

    Args:
        input1:         Raw text or source code of file 1
        input2:         Raw text or source code of file 2
        mode:           'text' or 'code'
        lang1_override: Optional. Force language for file 1 ('python', 'java', 'cpp').
                        If None, auto-detection is used.
        lang2_override: Optional. Force language for file 2 ('python', 'java', 'cpp').
                        If None, auto-detection is used.

    Returns:
        dict with keys: mode, language, scores, final_similarity, risk_level
    """

    if mode == "text":
        result      = compare_texts(input1, input2)
        final_score = result["final_similarity"]

        return {
            "mode":     "text",
            "language": "english",
            "scores": {
                "jaccard":    result.get("jaccard"),
                "cosine":     result.get("cosine"),
                "winnowing":  None,
                "lcs":        result.get("lcs"),
                "ast":        None
            },
            "final_similarity": final_score,
            "risk_level":       classify_risk(final_score)
        }

    elif mode == "code":
        # Use override if provided, otherwise auto-detect
        lang1 = lang1_override.lower() if lang1_override else detect_language(input1)
        lang2 = lang2_override.lower() if lang2_override else detect_language(input2)

        logger.info("Code comparison — detected/overridden languages: %s | %s", lang1, lang2)

        result      = compare_code(input1, input2, lang1=lang1, lang2=lang2)
        final_score = result["final_code_similarity"]

        return {
            "mode":     "code",
            "language": f"{lang1}/{lang2}" if lang1 != lang2 else lang1,
            "scores": {
                "jaccard":   None,
                "cosine":    None,
                "winnowing": result.get("winnowing"),
                "lcs":       result.get("lcs"),
                "ast":       result.get("ast")
            },
            "final_similarity": final_score,
            "risk_level":       classify_risk(final_score)
        }

    else:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'text' or 'code'.")