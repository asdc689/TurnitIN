def aggregate_text_score(jaccard, lcs, cosine):
    """
    Weighted aggregation of similarity scores
    """

    # these weights can be changed as per requirement
    w_jaccard = 0.2
    w_lcs = 0.2
    w_cosine = 0.6

    final_score = (
        w_jaccard * jaccard +
        w_lcs * lcs +
        w_cosine * cosine
    )

    return final_score
