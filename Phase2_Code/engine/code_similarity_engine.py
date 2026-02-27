import logging

from Phase2_Code.code_preprocess.clean_code import clean_code
from Phase2_Code.code_preprocess.code_tokenizer import tokenize_code, normalize_identifiers
from Phase2_Code.algorithms.rabin_karp import similarity_score as winnowing_similarity
from Phase2_Code.algorithms.code_lcs import lcs_similarity
from Phase2_Code.algorithms.ast_similarity import ast_similarity
from Phase2_Code.scoring.code_aggregate import aggregate_code_score

logger = logging.getLogger(__name__)


def compare_code(code1: str, code2: str, lang1: str, lang2: str) -> dict:
    """
    Full pipeline: clean → tokenize → normalize → score → aggregate.
    lang1 and lang2 must be 'python', 'java', or 'cpp'.
    """

    # 1. CLEANING (language-aware)
    clean1 = clean_code(code1, lang=lang1)
    clean2 = clean_code(code2, lang=lang2)

    # 2. TOKENIZATION + IDENTIFIER NORMALIZATION
    tokens1 = normalize_identifiers(tokenize_code(clean1, lang=lang1), lang=lang1)
    tokens2 = normalize_identifiers(tokenize_code(clean2, lang=lang2), lang=lang2)

    # 3. TOKEN-BASED SCORES
    w_score = winnowing_similarity(tokens1, tokens2)
    l_score = lcs_similarity(tokens1, tokens2)

    # 4. AST SCORE — only valid for same-language comparisons
    if lang1.lower() == lang2.lower():
        try:
            a_score = ast_similarity(code1, code2, lang1.lower())
        except Exception as e:
            logger.warning("AST calculation failed for lang=%s: %s", lang1, e)
            a_score = 0.0
    else:
        # Cross-language: AST is structurally incompatible
        a_score = None

    # 5. AGGREGATION
    final_score = aggregate_code_score(w_score, l_score, a_score)

    return {
        "winnowing":            round(w_score, 4),
        "lcs":                  round(l_score, 4),
        "ast":                  None if a_score is None else round(a_score, 4),
        "final_code_similarity": final_score
    }