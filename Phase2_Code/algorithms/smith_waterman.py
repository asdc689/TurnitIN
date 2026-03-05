def local_alignment_score(
    tokens_a: list,
    tokens_b: list,
    match_award=2,
    mismatch_penalty=-1,
    gap_penalty=-1,
    min_block_lines=3,
    min_block_score=0.15,
    max_blocks=10,
):
    """
    Iterative Smith-Waterman algorithm.
    Finds multiple matched blocks between two token lists.
    tokens_a and tokens_b should be lists of tuples: (token_string, line_number)
    """
    if not tokens_a or not tokens_b:
        return {"blocks": []}

    # Cap lengths to prevent memory spikes on massive files
    MAX_LEN = 8000
    tokens_a = tokens_a[:MAX_LEN]
    tokens_b = tokens_b[:MAX_LEN]
    n, m = len(tokens_a), len(tokens_b)

    max_possible = min(n, m) * match_award
    if max_possible == 0:
        return {"blocks": []}

    # ── Build initial score matrix ────────────────────────────────────────────
    def build_matrix(ta, tb, used_a, used_b):
        matrix = [[0] * (m + 1) for _ in range(n + 1)]
        max_score = 0
        max_pos   = (0, 0)

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                # Skip cells that belong to already-used regions
                if i - 1 in used_a or j - 1 in used_b:
                    matrix[i][j] = 0
                    continue

                if ta[i-1][0] == tb[j-1][0]:
                    match = matrix[i-1][j-1] + match_award
                else:
                    match = matrix[i-1][j-1] + mismatch_penalty

                delete = matrix[i-1][j] + gap_penalty
                insert = matrix[i][j-1] + gap_penalty

                score = max(0, match, delete, insert)
                matrix[i][j] = score

                if score > max_score:
                    max_score = score
                    max_pos   = (i, j)

        return matrix, max_score, max_pos

    # ── Traceback a single block ──────────────────────────────────────────────
    def traceback(matrix, max_pos, ta, tb):
        i, j = max_pos

        end_line_a = ta[i-1][1]
        end_line_b = tb[j-1][1]

        indices_a = []
        indices_b = []

        while i > 0 and j > 0 and matrix[i][j] > 0:
            indices_a.append(i - 1)
            indices_b.append(j - 1)

            if ta[i-1][0] == tb[j-1][0]:
                i -= 1
                j -= 1
            else:
                if matrix[i-1][j] > matrix[i][j-1]:
                    i -= 1
                else:
                    j -= 1

        if not indices_a or not indices_b:
            return None, set(), set()

        start_line_a = ta[indices_a[-1]][1]
        start_line_b = tb[indices_b[-1]][1]

        return (start_line_a, end_line_a, start_line_b, end_line_b), set(indices_a), set(indices_b)

    # ── Iterative block extraction ────────────────────────────────────────────
    blocks  = []
    used_a  = set()
    used_b  = set()

    for _ in range(max_blocks):
        matrix, max_score, max_pos = build_matrix(tokens_a, tokens_b, used_a, used_b)

        # Stop if no meaningful alignment found
        if max_score == 0:
            break

        block_score = max_score / max_possible
        if block_score < min_block_score:
            break

        region, new_used_a, new_used_b = traceback(matrix, max_pos, tokens_a, tokens_b)

        if region is None:
            break

        start_line_a, end_line_a, start_line_b, end_line_b = region

        # Filter out blocks smaller than min_block_lines
        lines_a = end_line_a - start_line_a + 1
        lines_b = end_line_b - start_line_b + 1

        if lines_a >= min_block_lines and lines_b >= min_block_lines:
            blocks.append({
                "score":         round(block_score * 100, 2),
                "file_a_region": [start_line_a, end_line_a],
                "file_b_region": [start_line_b, end_line_b],
            })

        # Mark these indices as used regardless of whether block passed filter
        used_a.update(new_used_a)
        used_b.update(new_used_b)

        # Stop if we've covered most of the file
        if len(used_a) > n * 0.85 or len(used_b) > m * 0.85:
            break

    return {"blocks": blocks}