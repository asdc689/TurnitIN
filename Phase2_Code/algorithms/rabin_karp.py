import hashlib

def get_kgrams(tokens: list, k: int):
    """Generates k-grams from a list of token strings."""
    return ["".join(tokens[i:i+k]) for i in range(len(tokens) - k + 1)]

def hash_kgram(kgram: str):
    """Uses MD5 for stable hashing across different runs/workers."""
    return int(hashlib.md5(kgram.encode('utf-8')).hexdigest(), 16)

def winnowing(hashes: list, window_size: int):
    """
    The core Winnowing algorithm. 
    Slides a window over the hashes and selects the minimum hash in each window
    to create a document fingerprint.
    """
    fingerprints = set()
    if not hashes:
        return fingerprints
        
    # If the file is smaller than the window, just return the min hash
    if len(hashes) < window_size:
        fingerprints.add(min(hashes))
        return fingerprints

    # Slide the window and pick the minimum hash
    for i in range(len(hashes) - window_size + 1):
        window = hashes[i:i+window_size]
        fingerprints.add(min(window))
        
    return fingerprints

def similarity_score(tokens1: list, tokens2: list, k: int = 3, window_size: int = 4) -> float:
    """
    Calculates Jaccard similarity using Winnowing, with safety nets for tiny files.
    """
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0

    # SAFETY NET: If the code is smaller than the k-gram size, fallback to basic Jaccard
    if len(tokens1) < k or len(tokens2) < k:
        set1, set2 = set(tokens1), set(tokens2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    # 1. Generate k-grams
    kgrams_a = get_kgrams(tokens1, k)
    kgrams_b = get_kgrams(tokens2, k)

    # 2. Hash k-grams
    hashes_a = [hash_kgram(kg) for kg in kgrams_a]
    hashes_b = [hash_kgram(kg) for kg in kgrams_b]

    # 3. Create Fingerprints
    fp_a = winnowing(hashes_a, window_size)
    fp_b = winnowing(hashes_b, window_size)

    # 4. Calculate Jaccard Similarity
    intersection = len(fp_a.intersection(fp_b))
    union = len(fp_a.union(fp_b))

    return intersection / union if union > 0 else 0.0