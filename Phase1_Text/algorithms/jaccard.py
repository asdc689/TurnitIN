# Set based similarity detection.

def jaccard_similarity(tokens1, tokens2):
    set1 = set(tokens1)
    set2 = set(tokens2)

    # Edge case: both empty
    if not set1 and not set2:
        return 1.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    return len(intersection) / len(union)

