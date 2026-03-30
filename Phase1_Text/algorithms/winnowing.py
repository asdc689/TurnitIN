"""
winnowing.py
------------
Implements the Winnowing algorithm for document fingerprinting.
This is the primary similarity signal — catches exact and near-exact matches
as well as copy-paste with minor modifications.

Reference: Schleimer, Wilkerson & Aiken (2003) — "Winnowing: Local Algorithms
for Document Fingerprinting", SIGMOD.
"""


# ── Tunable Parameters ────────────────────────────────────────────────────────
# K: n-gram size. Larger = more precise, fewer false positives, but misses
#    short copied passages. Smaller = more sensitive but noisier.
#    Recommended range: 5–8 for word-grams, 30–50 for char-grams.
DEFAULT_K = 6

# WINDOW_SIZE: Size of the sliding hash window. Controls density of
# fingerprints selected. Larger window = fewer fingerprints = faster but
# less precise. Smaller = denser coverage.
DEFAULT_WINDOW = 5

# HASH_MOD: Modulus for the rolling hash to keep values bounded.
HASH_MOD = (1 << 32)  # 2^32

# Base for polynomial rolling hash
HASH_BASE = 31
# ─────────────────────────────────────────────────────────────────────────────


def _build_kgrams(tokens: list[str], k: int) -> list[str]:
    """
    Build word-level k-grams from a token list.
    Each k-gram is a single string of k consecutive words joined by space.
    Example: tokens=["the","quick","brown","fox"], k=3
             → ["the quick brown", "quick brown fox"]
    """
    return [" ".join(tokens[i:i+k]) for i in range(len(tokens) - k + 1)]


def _hash_kgram(kgram: str) -> int:
    """
    Polynomial rolling hash of a k-gram string.
    Deterministic and fast.
    """
    h = 0
    for ch in kgram:
        h = (h * HASH_BASE + ord(ch)) % HASH_MOD
    return h


def _hash_all_kgrams(kgrams: list[str]) -> list[int]:
    """Hash every k-gram in the list."""
    return [_hash_kgram(kg) for kg in kgrams]


def _winnow(hash_sequence: list[int], window_size: int) -> set[int]:
    """
    Core Winnowing selection step.
    Slides a window of size `window_size` over the hash sequence.
    In each window, records the MINIMUM hash value (with its position).
    If the minimum shifts, the new minimum is added to the fingerprint set.

    FIX: Original used list.pop(0) which is O(n) per slide — O(n²) total.
    Replaced with collections.deque for O(1) pops from both ends.

    Returns a set of selected hash values (the document fingerprint).
    """
    from collections import deque

    if not hash_sequence:
        return set()

    fingerprints = set()
    window = deque()           # stores (hash_value, position)
    current_min = (float("inf"), -1)

    for i, h in enumerate(hash_sequence):
        window.append((h, i))

        if len(window) == window_size:
            win_min = min(window, key=lambda x: x[0])

            if win_min != current_min:
                current_min = win_min
                fingerprints.add(current_min[0])

            window.popleft()   # O(1) with deque, was O(n) with list.pop(0)

    # Process remaining partial window at the end
    if window:
        win_min = min(window, key=lambda x: x[0])
        if win_min != current_min:
            fingerprints.add(win_min[0])

    return fingerprints


def fingerprint(tokens: list[str], k: int = DEFAULT_K, window: int = DEFAULT_WINDOW) -> set[int]:
    """
    Full Winnowing pipeline: tokens → k-grams → hashes → fingerprint set.

    Args:
        tokens:  Preprocessed word token list from preprocessor.py
        k:       K-gram size
        window:  Winnowing window size

    Returns:
        A set of integer hash values representing the document's fingerprint.
    """
    if len(tokens) < k:
        # Document too short to form a k-gram — fall back to hashing
        # the whole token sequence as a single fingerprint
        return {_hash_kgram(" ".join(tokens))}

    kgrams = _build_kgrams(tokens, k)
    hashes = _hash_all_kgrams(kgrams)
    return _winnow(hashes, window)


def winnowing_similarity(fp_a: set[int], fp_b: set[int]) -> float:
    """
    Compute Jaccard similarity between two fingerprint sets.

    Jaccard = |A ∩ B| / |A U B|

    Returns a float in [0.0, 1.0].
    1.0 = identical fingerprints, 0.0 = no overlap at all.
    """
    if not fp_a or not fp_b:
        return 0.0  # Any empty fingerprint → no match possible

    intersection = len(fp_a & fp_b)
    union = len(fp_a | fp_b)
    return intersection / union


def get_matched_kgrams(tokens_a: list[str], tokens_b: list[str],
                       k: int = DEFAULT_K) -> list[str]:
    """
    Returns the list of k-grams that appear in BOTH documents.
    Useful for highlighting which exact phrases were matched.
    """
    kgrams_a = set(_build_kgrams(tokens_a, k))
    kgrams_b = set(_build_kgrams(tokens_b, k))
    return sorted(kgrams_a & kgrams_b)
