"""
keyword_analysis.py
-------------------
Three complementary signals that dramatically improve detection when
Winnowing misses paraphrased content (because n-grams don't match):

1. CONTENT-WORD JACCARD
   Strip stop words, get the set of unique content words in each document,
   compute Jaccard overlap. Words shared between documents — even scattered
   across rewritten sentences — are caught here. Paraphrasing rarely changes
   every single domain keyword ("emissions", "fossil", "climate", "ocean",
   "neural", "algorithm" etc.), so this is effective even under heavy rewording.

2. CHARACTER N-GRAM JACCARD
   Build character n-grams (default n=5) across the full normalized text of
   each document and compute Jaccard. Morphologically similar words share
   character n-grams: "temperatures" and "temperature" share "tempe", "emper",
   "mper", "perat", "erat", "ratu", "atur", "ture". This bridges the gap
   between surface-level word matching and true semantic similarity.
   Works especially well when the same root words appear in different forms.

3. NUMERIC ANCHOR MATCHING
   Numbers, percentages, measurements, and statistics are almost never changed
   in plagiarism (because changing them would change the meaning entirely).
   Extract every numeric token from both documents and compute overlap ratio.
   "342 participants" → "342 subjects" still shares 342. p < 0.001 appears
   in both. This is a very strong and precise signal for academic/technical
   plagiarism.
"""

import re
from Phase1_Text.preprocess.preprocessor import STOP_WORDS


# ── 1. Content-Word Jaccard ───────────────────────────────────────────────────

def _extract_content_words(tokens: list[str]) -> set[str]:
    """
    Return the SET of unique content words (non-stop words, len >= 3).
    Using a set means we care about vocabulary overlap, not frequency.
    Min length 3 filters out short particles that survived stop-word removal.
    """
    return {t for t in tokens if t not in STOP_WORDS and len(t) >= 3}


def keyword_jaccard(tokens_a: list[str], tokens_b: list[str]) -> float:
    """
    Jaccard similarity on the set of unique content words.

    Effective for: paraphrasing that preserves domain vocabulary, synonym
    substitution that misses some keywords, any case where technical terms
    survive rewording (e.g., "neural network", "photosynthesis", "emissions").

    Returns float in [0.0, 1.0].
    """
    words_a = _extract_content_words(tokens_a)
    words_b = _extract_content_words(tokens_b)

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


# ── 2. Character N-Gram Jaccard ───────────────────────────────────────────────

def _build_char_ngrams(text: str, n: int = 5) -> set[str]:
    """
    Build the SET of unique character n-grams from a normalized text string.
    Spaces are removed first so word boundaries don't fragment n-grams.
    """
    text = re.sub(r"\s+", "", text)  # remove spaces
    if len(text) < n:
        return {text}
    return {text[i:i+n] for i in range(len(text) - n + 1)}


def char_ngram_similarity(text_a: str, text_b: str, n: int = 5) -> float:
    """
    Jaccard similarity on character n-gram sets.

    Captures morphological similarity that word-level comparison misses:
    - "temperatures" ↔ "temperature" share 9 of 11 5-grams
    - "burning" ↔ "combustion" share fewer but "emissions" ↔ "emissions" = 100%
    - Particularly useful for scientific vocabulary with shared Latin/Greek roots.

    n=5 is a good balance: specific enough to avoid noise (function words are
    only 3-4 chars so 5-grams filter most of them), broad enough to catch
    morphological variants.

    Returns float in [0.0, 1.0].
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    ngrams_a = _build_char_ngrams(text_a, n)
    ngrams_b = _build_char_ngrams(text_b, n)

    if not ngrams_a or not ngrams_b:
        return 0.0

    intersection = len(ngrams_a & ngrams_b)
    union = len(ngrams_a | ngrams_b)
    return intersection / union if union > 0 else 0.0


# ── 3. Numeric Anchor Matching ────────────────────────────────────────────────

def _extract_numerics(text: str) -> list[str]:
    """
    Extract all numeric tokens from text:
    - Integers: 342, 1915
    - Decimals: 3.14, 0.001
    - Percentages: 34%, 18%
    - Measurements: 200mg, 100ml, 12km (number + unit fused)
    - Scientific notation: 1e-5
    Returns them as normalized strings (lowercased, stripped).
    """
    # Expanded pattern covers:
    #   - Currency prefixes: $1200, $1,200
    #   - Comma-separated thousands: 1,000,000
    #   - Decimals and scientific notation: 3.14, 1e-5
    #   - Stat expressions: p<0.05, r=0.87 (captures the number part)
    #   - Percentages and measurement units fused to number
    # Strip commas from matches so "1,200" and "1200" are treated as identical.
    pattern = (
        r"(?:[\$\£\€])?\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:e[+-]?\d+)?"
        r"(?:%|mg|ml|kg|km|cm|mm|lb|oz|hz|ghz|mhz)?\b"
        r"|"
        r"\b\d+(?:\.\d+)?(?:e[+-]?\d+)?(?:%|mg|ml|kg|km|cm|mm|lb|oz|hz|ghz|mhz)?\b"
    )
    raw = re.findall(pattern, text.lower())
    # Normalise: remove commas so 1,200 == 1200
    return [n.replace(",", "") for n in raw if n.strip()]


def numeric_anchor_score(text_a: str, text_b: str) -> float:
    """
    Measure overlap of numeric tokens between two texts.

    Numbers in academic/technical writing are extremely strong plagiarism
    anchors — they almost never change in paraphrasing because altering them
    would change the factual claim. "342 participants", "p < 0.001",
    "34% reduction" — if these appear in both documents, that's highly
    suspicious regardless of how different the surrounding prose is.

    Returns:
        Float in [0.0, 1.0] representing the fraction of numeric tokens in
        document A that also appear in document B.
        Returns 0.0 if neither document contains numeric tokens
        (avoids artificially boosting non-numeric text).
    """
    nums_a = _extract_numerics(text_a)
    nums_b = _extract_numerics(text_b)

    # If neither doc has numbers, this signal is not applicable — return 0
    # so it doesn't artificially boost non-technical documents.
    if not nums_a and not nums_b:
        return 0.0

    # If one has numbers and the other doesn't, that's a mismatch
    if not nums_a or not nums_b:
        return 0.0

    set_a = set(nums_a)
    set_b = set(nums_b)

    # Use the smaller set as denominator to be conservative
    # (we care whether the numbers from A appear in B)
    matching = len(set_a & set_b)
    base = min(len(set_a), len(set_b))
    return matching / base if base > 0 else 0.0


def run_all_keyword_signals(text_a: str, text_b: str,
                             tokens_a: list[str], tokens_b: list[str]) -> dict:
    """
    Run all three signals and return results in a single dict.
    This is what scorer.py calls.
    """
    kw_score = keyword_jaccard(tokens_a, tokens_b)
    char_score = char_ngram_similarity(text_a, text_b)
    num_score = numeric_anchor_score(text_a, text_b)

    # Dynamic weighting: numeric anchor gets high weight ONLY when numbers
    # are present in at least one document. When neither document has numbers,
    # renormalize across just keyword_jaccard + char_ngram so that
    # identical non-numeric docs still score keyword_combined = 1.0.
    nums_a = _extract_numerics(text_a)
    nums_b = _extract_numerics(text_b)
    has_numbers = bool(nums_a or nums_b)

    if has_numbers:
        w_kw, w_char, w_num = 0.35, 0.20, 0.45
        combined = (kw_score * w_kw) + (char_score * w_char) + (num_score * w_num)
    else:
        # Renormalize kw and char weights dynamically so they always sum to 1.0.
        # Derived from the has_numbers branch: kw=0.35, char=0.20 → total=0.55
        # Scaling: kw_norm = 0.35/0.55, char_norm = 0.20/0.55
        w_kw, w_char = 0.35, 0.20
        total = w_kw + w_char
        combined = (kw_score * w_kw / total) + (char_score * w_char / total)

    return {
        "keyword_jaccard":    round(kw_score, 4),
        "char_ngram":         round(char_score, 4),
        "numeric_anchor":     round(num_score, 4),
        "combined":           round(combined, 4),
    }
