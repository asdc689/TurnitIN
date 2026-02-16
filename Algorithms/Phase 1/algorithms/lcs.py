def lcs_similarity(a, b):
    n, m = len(a), len(b)

    # Edge cases
    if n == 0 or m == 0:
        return 0.0

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Build DP
    for i in range(n):
        for j in range(m):
            if a[i] == b[j]:
                dp[i+1][j+1] = dp[i][j] + 1
            else:
                dp[i+1][j+1] = max(dp[i][j+1], dp[i+1][j])

    lcs_length = dp[n][m]
    return lcs_length / min(n, m)   # normalized score


if __name__ == "__main__":
    A = ["this", "is", "a", "test"]
    B = ["this", "is", "test"]

    print("LCS Similarity:", lcs_similarity(A, B))
