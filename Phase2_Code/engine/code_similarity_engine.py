import logging
from Phase2_Code.universal_parser import UniversalParser
from Phase2_Code.algorithms.semantic_embedding import SemanticEmbedder
from Phase2_Code.algorithms.ast_edit_distance import ast_sequence_similarity
from Phase2_Code.algorithms.smith_waterman import local_alignment_score
from Phase2_Code.algorithms.code_lcs import lcs_similarity
from Phase2_Code.algorithms.rabin_karp import similarity_score as winnowing_score

logger = logging.getLogger(__name__)

# ── Lazy Loaders (only initialize when first code submission arrives) ─────────

_PARSER = None
_EMBEDDER = None

def _get_parser():
    global _PARSER
    if _PARSER is None:
        logger.info("Initializing UniversalParser...")
        _PARSER = UniversalParser()
    return _PARSER

def _get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        logger.info("Loading Jina embedding model (first code submission)...")
        _EMBEDDER = SemanticEmbedder()
    return _EMBEDDER


# ── Main Entry Point ──────────────────────────────────────────────────────────

def compare_code(code1: str, code2: str, lang1: str, lang2: str) -> dict:
    logger.info("Running Engine...")

    data_a = _get_parser().parse(code1, lang1)
    data_b = _get_parser().parse(code2, lang2)

    is_cross_lang = lang1.lower() != lang2.lower()

    sw_result     = local_alignment_score(data_a["tokens"], data_b["tokens"])
    blocks        = sw_result.get("blocks", [])
    sw_score      = max((b["score"] / 100 for b in blocks), default=0.0)

    if is_cross_lang:
        vectors      = _get_embedder().encode_batch([code1, code2])
        semantic_sim = _get_embedder().calculate_similarity(vectors[0], vectors[1])

        cf_a, cf_b = data_a["cf_signature"], data_b["cf_signature"]
        cf_diff    = abs(len(cf_a) - len(cf_b))
        max_cf     = max(len(cf_a), len(cf_b))
        cf_penalty = (cf_diff / max_cf) * 0.3 if max_cf > 0 else 0.0
        adjusted_semantic = max(0.0, semantic_sim - cf_penalty)

        cfg_lcs_score = lcs_similarity(cf_a, cf_b)
        global_score  = (0.80 * adjusted_semantic) + (0.20 * cfg_lcs_score)
        final_score   = max(global_score, sw_score)

        w_score, l_score, a_score = None, cfg_lcs_score, None

    else:
        tokens_a_str = [t[0] for t in data_a["tokens"]]
        tokens_b_str = [t[0] for t in data_b["tokens"]]

        w_score      = winnowing_score(tokens_a_str, tokens_b_str)
        ast_score    = ast_sequence_similarity(data_a["ast_sequence"], data_b["ast_sequence"])
        l_score      = lcs_similarity(tokens_a_str, tokens_b_str)

        global_score = (0.35 * w_score) + (0.35 * ast_score) + (0.30 * l_score)
        final_score  = max(global_score, sw_score)

        a_score = ast_score

    return {
        "winnowing":             round(w_score, 4) if w_score is not None else None,
        "lcs":                   round(l_score, 4) if l_score is not None else None,
        "ast":                   round(a_score, 4) if a_score is not None else None,
        "final_code_similarity": round(final_score, 4),
        "matched_blocks":        blocks if blocks else None
    }