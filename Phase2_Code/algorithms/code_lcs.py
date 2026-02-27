def lcs_length(seq1, seq2):
    n, m = len(seq1), len(seq2)

    if n == 0 or m == 0:
        return 0

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[n][m]


def lcs_similarity(tokens1, tokens2):
    """
    Normalized LCS similarity for code tokens
    """
    if not tokens1 or not tokens2:
        return 0.0

    lcs_len = lcs_length(tokens1, tokens2)
    return lcs_len / min(len(tokens1), len(tokens2))
