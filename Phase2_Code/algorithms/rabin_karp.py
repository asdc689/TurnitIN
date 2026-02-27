import hashlib

def stable_hash(token):
    return int(hashlib.md5(token.encode()).hexdigest(), 16)

def rabin_karp_fingerprints(tokens, k=3):
    if k <= 0:
        raise ValueError("k must be a positive integer")

    base = 256
    mod = 10**9 + 7

    hashes = []
    n = len(tokens)

    if n < k:
        return hashes

    # Convert tokens to numbers
    token_ids = [stable_hash(t) % mod for t in tokens]

    # Initial hash for the first k-gram
    # power = base^(k-1) needed to remove the leftmost element in rolling hash
    h = 0
    power = pow(base, k - 1, mod)
    for i in range(k):
        h = (h * base + token_ids[i]) % mod

    hashes.append(h)

    # Rolling hash across subsequent k-grams
    for i in range(k, n):
        h = (h * base - token_ids[i - k] * power + token_ids[i]) % mod
        h = (h + mod) % mod
        hashes.append(h)

    return hashes

def winnowing(fingerprints, window_size=4):
    """
    Selects minimum hash in each window (Winnowing algorithm)
    """
    if not fingerprints:
        return set()

    if window_size <= 0:
        raise ValueError("window_size must be positive")

    selected = set()
    n = len(fingerprints)

    if n <= window_size:
        return set(fingerprints)

    for i in range(n - window_size + 1):
        window = fingerprints[i:i + window_size]
        selected.add(min(window))

    return selected

def similarity_score(tokens1, tokens2, k=3, window_size=4):
    if k <= 0:
        raise ValueError("k must be a positive integer")

    f1 = rabin_karp_fingerprints(tokens1, k)
    f2 = rabin_karp_fingerprints(tokens2, k)

    w1 = winnowing(f1, window_size)
    w2 = winnowing(f2, window_size)

    if not w1 or not w2:
        return 0.0

    return len(w1 & w2) / len(w1 | w2)
