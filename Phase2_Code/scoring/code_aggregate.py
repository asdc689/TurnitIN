def aggregate_code_score(
    winnowing_score,
    lcs_score,
    ast_score
):
    """
    Weighted aggregation of code plagiarism scores
    AST may be None for cross-language comparisons.
    """

    # ---------- Cross-language case ----------
    if ast_score is None:
        # AST is unreliable across languages
        # Rely more on LCS (algorithmic similarity)
        return round(0.8 * lcs_score + 0.2 * winnowing_score, 4)
    

    # ---------- Same-language case ----------
    w_winnowing = 0.4   # strongest signal (copied fragments)
    w_lcs = 0.3         # structural similarity
    w_ast = 0.3         # logic similarity

    final_score = (
        w_winnowing * winnowing_score +
        w_lcs * lcs_score +
        w_ast * ast_score
    )

    return round(final_score, 4)
