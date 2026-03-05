def ast_sequence_similarity(seq_a: list, seq_b: list) -> float:
    """
    Calculates structural similarity using sequence edit distance.
    Runs in O(N*M) time. Highly effective for catching refactored code.
    """
    if not seq_a and not seq_b:
        return 1.0
    if not seq_a or not seq_b:
        return 0.0

    # Cap maximum sequence length to prevent RAM/CPU spikes on massive files
    MAX_LEN = 8000
    seq_a, seq_b = seq_a[:MAX_LEN], seq_b[:MAX_LEN]
    n, m = len(seq_a), len(seq_b)

    # 1D array optimization for Edit Distance
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if seq_a[i-1] == seq_b[j-1]:
                curr[j] = prev[j-1]
            else:
                curr[j] = 1 + min(prev[j], curr[j-1], prev[j-1]) # Insert, Delete, Replace
        prev = curr

    edit_distance = prev[m]
    max_possible_distance = max(n, m)
    
    # Convert edit distance to a percentage similarity
    similarity = 1.0 - (edit_distance / max_possible_distance)
    return max(0.0, similarity)