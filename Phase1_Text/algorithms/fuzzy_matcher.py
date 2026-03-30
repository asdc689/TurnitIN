"""
fuzzy_matcher.py
----------------
Fuzzy sentence-level matching using edit distance (Levenshtein).

This catches cases that slip through Winnowing and TF-IDF:
  - Minor word substitutions ("big" → "large", "said" → "stated")
  - Slight reordering within a sentence
  - Typo-masked plagiarism

It's the cheapest layer to run (pure stdlib, no dependencies) and acts
as a final sweep after the main signals have been computed.
"""

import re


def _levenshtein(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein (edit) distance between two strings.
    Uses the space-optimized two-row DP approach — O(min(m,n)) space.
    """
    if s1 == s2:
        return 0
    if len(s1) < len(s2):
        s1, s2 = s2, s1  # ensure s1 is the longer string

    len1, len2 = len(s1), len(s2)
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            curr[j] = min(
                prev[j] + 1,        # deletion
                curr[j-1] + 1,      # insertion
                prev[j-1] + cost,   # substitution
            )
        prev, curr = curr, [0] * (len2 + 1)

    return prev[len2]


def normalized_edit_similarity(s1: str, s2: str) -> float:
    """
    Edit distance normalized to [0, 1].
    1.0 = identical, 0.0 = completely different.

    Normalized by the length of the longer string so that short sentences
    are not unfairly penalized.
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    max_len = max(len(s1), len(s2))
    dist = _levenshtein(s1, s2)
    return 1.0 - (dist / max_len)


def _normalize_sentence(sent: str) -> str:
    """Lowercase, strip punctuation and extra whitespace for comparison."""
    sent = sent.lower()
    sent = re.sub(r"[^\w\s]", "", sent)
    sent = re.sub(r"\s+", " ", sent).strip()
    return sent


def fuzzy_sentence_matches(sentences_a: list[str],
                            sentences_b: list[str],
                            threshold: float = 0.75) -> dict:
    """
    For each sentence in A, find the most edit-similar sentence in B.
    Only reports pairs above the similarity threshold.

    FIX 1: Added length-ratio pre-filter. If two sentences differ in length
    by more than 2x, their edit similarity is mathematically bounded below
    the threshold — skip the expensive O(m*n) Levenshtein entirely.

    FIX 2: Added short-sentence guard. Sentences under 10 chars produce
    unreliable edit-distance scores (single word changes dominate) and
    generate false positives. They are skipped.
    """
    if not sentences_a or not sentences_b:
        return {"mean_score": 0.0, "max_score": 0.0, "matches": [], "match_ratio": 0.0}

    norm_b = [_normalize_sentence(s) for s in sentences_b]

    best_scores = []
    matched_sentences = []

    for sent_a in sentences_a:
        norm_a = _normalize_sentence(sent_a)
        if not norm_a or len(norm_a) < 10:   # FIX 2: skip very short sentences
            continue

        best_score = 0.0
        best_j = 0
        len_a = len(norm_a)

        for j, nb in enumerate(norm_b):
            if not nb:
                continue

            # FIX 1: Length-ratio pre-filter — saves Levenshtein for hopeless pairs
            len_b = len(nb)
            longer = max(len_a, len_b)
            shorter = min(len_a, len_b)
            # If shorter/longer < (1 - threshold), max possible similarity < threshold
            if shorter / longer < (1.0 - threshold):
                continue

            score = normalized_edit_similarity(norm_a, nb)
            if score > best_score:
                best_score = score
                best_j = j

        best_scores.append(best_score)

        if best_score >= threshold:
            matched_sentences.append((
                sent_a,
                sentences_b[best_j],
                round(best_score, 4),
            ))

    mean_score = sum(best_scores) / len(best_scores) if best_scores else 0.0
    max_score = max(best_scores) if best_scores else 0.0
    match_ratio = len(matched_sentences) / len(sentences_a) if sentences_a else 0.0

    return {
        "mean_score": round(mean_score, 4),
        "max_score": round(max_score, 4),
        "matches": matched_sentences,
        "match_ratio": round(match_ratio, 4),
    }
