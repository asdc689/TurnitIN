def lcs_similarity(list_a: list, list_b: list) -> float:
    """
    Calculates the Longest Common Subsequence between two lists.
    Used for checking the relative order of tokens or control flow blocks.
    """
    if not list_a and not list_b:
        return 1.0
    if not list_a or not list_b:
        return 0.0

    MAX_LEN = 8000
    list_a, list_b = list_a[:MAX_LEN], list_b[:MAX_LEN]
    n, m = len(list_a), len(list_b)

    # 1D array DP optimization to save RAM
    prev = [0] * (m + 1)
    
    for i in range(1, n + 1):
        curr = [0] * (m + 1)
        for j in range(1, m + 1):
            if list_a[i-1] == list_b[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = curr

    lcs_length = prev[m]
    
    # We divide by the max length to ensure 10 copied lines out of 1000 
    # doesn't give a high global score.
    max_possible = max(n, m)
    
    return lcs_length / max_possible if max_possible > 0 else 0.0