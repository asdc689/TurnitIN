from code_preprocess.clean_code import clean_code
from code_preprocess.code_tokenizer import tokenize_code, normalize_identifiers
from algorithms.rabin_karp import similarity_score as winnowing_similarity
from algorithms.code_lcs import lcs_similarity
from algorithms.ast_similarity import ast_similarity
from scoring.code_aggregate import aggregate_code_score

def compare_code(code1: str, code2: str, lang1="python", lang2="python"):
    # ---------- Preprocessing ----------
    clean1 = clean_code(code1)
    clean2 = clean_code(code2)

    tokens1 = normalize_identifiers(tokenize_code(clean1), lang1)
    tokens2 = normalize_identifiers(tokenize_code(clean2), lang2)

    # ---------- Algorithmic Scores ----------
    w_score = winnowing_similarity(tokens1, tokens2)
    l_score = lcs_similarity(tokens1, tokens2)

    # ---------- AST Score ----------
    # UPDATED: Now supports python, java, and cpp.
    # We pass the 'lang' variable directly to the function.
    if lang1.lower() == lang2.lower() :
        try:
            a_score = ast_similarity(code1, code2, lang1.lower())
        except Exception as e:
            print(f"AST calculation failed: {e}")
            a_score = 0.0
    else :
        # Cross-language → AST is NOT comparable
        a_score = None

    # ---------- Aggregation ----------
    final_score = aggregate_code_score(w_score, l_score, a_score)

    return {
        "winnowing": round(w_score, 4),
        "lcs": round(l_score, 4),
        "ast": None if a_score is None else round(a_score, 4),
        "final_code_similarity": final_score
    }