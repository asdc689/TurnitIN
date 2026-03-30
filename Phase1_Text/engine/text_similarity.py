"""
text_similarity.py
------------------
Engine entry point for text mode comparisons.
Called by Phase3_Unified.engine.unified_analyzer.

Returns a standardized dict compatible with the unified engine contract:
    {
        "final_similarity": float,
        "winnowing":        float | None,
        "jaccard":          float | None,
        "cosine":           float | None,
        "lcs":              float | None,
        "signal_breakdown": dict,
        "matched_content":  dict,
    }
"""

from Phase1_Text.engine.scorer import compute_similarity


def compare_texts(text1: str, text2: str) -> dict:
    """
    Run the full text similarity pipeline on two plain-text strings.

    Args:
        text1: Raw text content of document 1
        text2: Raw text content of document 2

    Returns:
        Standardized result dict for unified_analyzer.
    """
    report = compute_similarity(text1, text2)

    sb = report["signal_breakdown"]

    return {
        # Primary score consumed by unified_analyzer
        "final_similarity": report["summary"]["final_score"],

        # Per-algorithm scores surfaced in the API response
        # Winnowing replaces the old Jaccard fingerprint role
        "winnowing":  sb["winnowing_jaccard"],
        "tfidf":      sb["tfidf_document"],
        "semantic":   sb["semantic_sentence_mean"],
        "fuzzy":      sb["fuzzy_sentence_mean"],
        "synonym":    sb["synonym_score"],

        # Legacy keys kept for backward compat with unified_analyzer scores dict
        # (jaccard → keyword jaccard, cosine → tfidf_document, lcs → None)
        "jaccard": sb["keyword_jaccard"],
        "cosine":  sb["tfidf_document"],
        "lcs":     None,

        # Full breakdown passed through for detailed reporting
        "signal_breakdown": sb,
        "matched_content":  report["matched_content"],
        "document_stats":   report["document_stats"],
        "sbert_used":       report["summary"]["sbert_used"],
        "paraphrase_suspected": report["summary"]["paraphrase_suspected"],
    }