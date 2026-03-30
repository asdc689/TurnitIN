"""
preprocessor.py
---------------
Handles all text normalization before any comparison algorithm runs.
This is the most important step — garbage in, garbage out.

CHANGES vs original:
  - normalize_unicode: switched from NFKD+ASCII-strip to NFC so accented /
    non-English characters are preserved rather than silently dropped.
    Homoglyph spoofing (Cyrillic 'а' for Latin 'a') is still caught via a
    targeted substitution table.
  - tokenize: now accepts an optional apply_lemma flag. When enabled, tokens
    are run through NLTK's WordNetLemmatizer with POS tagging so inflected
    variants ("analyzed", "analyzes", "analysis") all collapse to the same
    real dictionary word ("analyze"). Unlike stemming, lemmatization always
    produces valid English words so there are no false root collisions.
  - preprocess: returns both raw tokens AND lemmatized_tokens so callers can
    choose the right representation for each signal.
"""

import re
import unicodedata
import string

# ── Lemmatizer setup (graceful fallback if NLTK not installed) ───────────────
_lemmatizer = None
_NLTK_AVAILABLE = False

try:
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet
    import nltk

    # Ensure required NLTK data is present
    for resource, path in [
        ("tokenizers/punkt",         "punkt"),
        ("corpora/wordnet",          "wordnet"),
        ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
        ("corpora/omw-1.4",          "omw-1.4"),
    ]:
        try:
            nltk.data.find(resource)
        except LookupError:
            nltk.download(path, quiet=True)

    _lemmatizer = WordNetLemmatizer()
    _NLTK_AVAILABLE = True
except ImportError:
    pass


def _get_wordnet_pos(treebank_tag: str) -> str:
    """
    Convert a Penn Treebank POS tag to a WordNet POS tag.
    WordNetLemmatizer needs this to lemmatize correctly.

    Without POS:  running → running  (assumes noun, stays unchanged)
    With POS:     running → run      (knows it's a verb)
    """
    if treebank_tag.startswith("J"):
        return wordnet.ADJ
    elif treebank_tag.startswith("V"):
        return wordnet.VERB
    elif treebank_tag.startswith("R"):
        return wordnet.ADV
    else:
        return wordnet.NOUN  # default


def lemmatize(word: str, pos_tag: str = "NN") -> str:
    """
    Return the lemmatized form of a word given its POS tag.
    Falls back to the original word if NLTK is not available.
    """
    if _NLTK_AVAILABLE and _lemmatizer:
        return _lemmatizer.lemmatize(word, _get_wordnet_pos(pos_tag))
    return word


def is_lemmatization_available() -> bool:
    return _NLTK_AVAILABLE


# Common stop words (English).
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "me", "him", "her", "us", "them", "my", "your", "his",
    "our", "their", "which", "who", "whom", "what", "when", "where", "how",
    "not", "no", "nor", "so", "yet", "both", "either", "neither", "as",
    "if", "then", "than", "too", "very", "just", "also", "about", "above",
    "after", "again", "all", "any", "because", "before", "between", "each",
    "few", "more", "most", "other", "over", "same", "such", "there", "through",
    "under", "until", "up", "while", "into", "during", "including", "without",
}

# Common Unicode homoglyphs — Cyrillic / Greek lookalikes mapped to Latin ASCII.
_HOMOGLYPH_TABLE = str.maketrans({
    "\u0430": "a",   # Cyrillic а → a
    "\u0435": "e",   # Cyrillic е → e
    "\u043e": "o",   # Cyrillic о → o
    "\u0440": "r",   # Cyrillic р → r
    "\u0441": "c",   # Cyrillic с → c
    "\u0445": "x",   # Cyrillic х → x
    "\u03b1": "a",   # Greek α → a
    "\u03b5": "e",   # Greek ε → e
    "\u03bf": "o",   # Greek ο → o
    "\u0456": "i",   # Cyrillic і → i
})


def normalize_unicode(text: str) -> str:
    """
    Normalize Unicode to NFC (canonical composition) so accented characters
    in legitimate multilingual text are preserved rather than stripped.

    Additionally applies a homoglyph substitution pass to catch the most
    common spoofing trick (Cyrillic / Greek lookalikes replacing Latin letters).
    """
    text = text.translate(_HOMOGLYPH_TABLE)
    return unicodedata.normalize("NFC", text)


def remove_punctuation(text: str) -> str:
    """Remove all punctuation marks."""
    return text.translate(str.maketrans("", "", string.punctuation))


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace (tabs, newlines, multiple spaces) to single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def split_into_sentences(text: str) -> list[str]:
    """
    Rule-based sentence splitter. Handles common abbreviations to avoid
    false splits (e.g., "Dr. Smith" should not split at the period).
    Returns a list of sentence strings.
    """
    ABBREVS = r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc|approx|dept|fig|est|vol|no)\."
    text = re.sub(ABBREVS, r"\1<PERIOD>", text, flags=re.IGNORECASE)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    sentences = [s.replace("<PERIOD>", ".").strip() for s in sentences if s.strip()]
    return sentences


def _lemmatize_tokens(tokens: list[str]) -> list[str]:
    """
    Lemmatize a list of tokens using POS-aware WordNet lemmatization.
    POS tags are computed once for the full token list via nltk.pos_tag,
    which is more accurate than tagging words in isolation.

    Example:
        ["running", "better", "studies"] →  ["run", "good", "study"]
    """
    if not _NLTK_AVAILABLE or not _lemmatizer:
        return tokens

    import nltk
    tagged = nltk.pos_tag(tokens)   # [(word, POS_tag), ...]
    return [
        _lemmatizer.lemmatize(word, _get_wordnet_pos(tag))
        for word, tag in tagged
    ]


def tokenize(text: str, remove_stops: bool = False,
             apply_lemma: bool = False) -> list[str]:
    """
    Lowercases, removes punctuation, splits into word tokens.

    Args:
        remove_stops:  Remove stop words (used for TF-IDF / keyword signals).
        apply_lemma:   Apply POS-aware lemmatization to collapse inflections
                       to real dictionary words.
                       Use for keyword_jaccard and winnowing.
                       Do NOT use for fuzzy matching (lemmas hurt edit distance).
    """
    text = text.lower()
    text = remove_punctuation(text)
    text = normalize_whitespace(text)
    tokens = text.split()
    if remove_stops:
        tokens = [t for t in tokens if t not in STOP_WORDS]
    if apply_lemma:
        tokens = _lemmatize_tokens(tokens)
    return tokens


def preprocess(text: str, remove_stops: bool = False) -> dict:
    """
    Master preprocessing function. Returns a dict with everything downstream
    modules need: normalized full text, sentences, raw tokens, and
    lemmatized tokens.

    lemmatized_tokens: POS-aware lemmatized version of tokens (if NLTK available).
    Used by keyword_jaccard and winnowing for better inflection coverage.
    Always produces valid English words — no meaningless stems.
    Falls back to plain tokens if NLTK is not installed.
    """
    # Step 1: Unicode normalization (NFC + homoglyph fix)
    text = normalize_unicode(text)

    # Step 2: Normalize whitespace
    text = normalize_whitespace(text)

    # Step 3: Split into sentences BEFORE lowercasing (sentence splitter
    # relies on capitalization for accuracy)
    sentences = split_into_sentences(text)

    # Step 4: Raw token list (lowercased, no punctuation, no lemmatization)
    tokens = tokenize(text, remove_stops=remove_stops, apply_lemma=False)

    # Step 5: Lemmatized token list — collapses inflections to dictionary words
    lemmatized_tokens = tokenize(text, remove_stops=remove_stops, apply_lemma=True)

    # Step 6: Normalized full text for character-level operations
    normalized_text = " ".join(tokens)

    return {
        "raw_text":           text,
        "normalized_text":    normalized_text,
        "sentences":          sentences,
        "tokens":             tokens,
        "lemmatized_tokens":  lemmatized_tokens,   # use for keyword/winnowing signals
        "lemma_active":       _NLTK_AVAILABLE,
    }