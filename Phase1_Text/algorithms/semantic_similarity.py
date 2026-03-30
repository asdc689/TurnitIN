"""
semantic_similarity.py
----------------------
Semantic sentence similarity using Sentence-BERT (SBERT).

This is the most powerful layer for detecting PARAPHRASING — cases where
someone rewrites sentences in their own words but the meaning is the same.
Fingerprinting and TF-IDF both fail here. SBERT catches it.

HOW IT WORKS:
  Each sentence is encoded into a dense 384-dimensional vector by a
  pretrained transformer model. Sentences with similar meaning will have
  vectors that point in similar directions. Cosine similarity between those
  vectors gives a meaning-based similarity score independent of wording.

SETUP:
  pip install sentence-transformers
  The model downloads automatically on first run (~90MB).
  Recommended model: 'all-MiniLM-L6-v2' — fast, small, excellent quality.

GRACEFUL FALLBACK:
  If sentence-transformers is not installed, this module falls back to
  the TF-IDF sentence cross-similarity from tfidf_similarity.py so the
  engine still works end-to-end without the transformer.
"""

import numpy as np

# Flag to track whether SBERT is available in this environment
_SBERT_AVAILABLE = False
_model = None

try:
    from sentence_transformers import SentenceTransformer
    _SBERT_AVAILABLE = True
except ImportError:
    pass


def _load_model(model_name: str = "all-MiniLM-L6-v2"):
    """Load the SBERT model once and cache it in memory."""
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def semantic_sentence_similarity(sentences_a: list[str],
                                  sentences_b: list[str],
                                  model_name: str = "all-MiniLM-L6-v2",
                                  threshold: float = 0.80) -> dict:
    """
    For each sentence in document A, find the most semantically similar
    sentence in document B using SBERT embeddings.

    Args:
        sentences_a:  Sentence list from document A
        sentences_b:  Sentence list from document B
        model_name:   SBERT model to use (default: all-MiniLM-L6-v2)
        threshold:    Cosine similarity threshold above which a sentence pair
                      is considered a semantic match. 0.80 is a good default —
                      high enough to filter noise, low enough to catch
                      moderate paraphrasing.

    Returns dict with:
        'mean_score':     Average of best-match scores across all sentences in A
        'max_score':      Highest single-pair similarity found
        'matches':        List of (sent_a, best_match_b, score) above threshold
        'match_ratio':    Fraction of sentences in A matched above threshold
        'used_sbert':     Boolean — True if SBERT was used, False if fallback
    """
    if not sentences_a or not sentences_b:
        return {
            "mean_score": 0.0, "max_score": 0.0,
            "matches": [], "match_ratio": 0.0, "used_sbert": False
        }

    if not _SBERT_AVAILABLE:
        # ── Graceful fallback to TF-IDF sentence similarity ──────────────────
        from Phase1_Text.algorithms.tfidf_similarity import sentence_cross_similarity
        result = sentence_cross_similarity(sentences_a, sentences_b)
        result["used_sbert"] = False
        return result

    # ── SBERT path ────────────────────────────────────────────────────────────
    model = _load_model(model_name)

    # Encode all sentences in one batched call for efficiency
    embeddings_a = model.encode(sentences_a, convert_to_numpy=True,
                                 show_progress_bar=False)
    embeddings_b = model.encode(sentences_b, convert_to_numpy=True,
                                 show_progress_bar=False)

    # Normalize embeddings (makes dot product == cosine similarity)
    norms_a = np.linalg.norm(embeddings_a, axis=1, keepdims=True)
    norms_b = np.linalg.norm(embeddings_b, axis=1, keepdims=True)
    embeddings_a = embeddings_a / np.maximum(norms_a, 1e-10)
    embeddings_b = embeddings_b / np.maximum(norms_b, 1e-10)

    # Full similarity matrix via vectorized dot product — shape (n_a, n_b)
    sim_matrix = np.dot(embeddings_a, embeddings_b.T)

    best_scores = []
    matched_sentences = []

    for i, row in enumerate(sim_matrix):
        best_j = int(np.argmax(row))
        best_score = float(row[best_j])
        best_score = np.clip(best_score, 0.0, 1.0)
        best_scores.append(best_score)

        if best_score >= threshold:
            matched_sentences.append((
                sentences_a[i],
                sentences_b[best_j],
                round(float(best_score), 4),
            ))

    mean_score = float(np.mean(best_scores)) if best_scores else 0.0
    max_score = float(np.max(best_scores)) if best_scores else 0.0
    match_ratio = len(matched_sentences) / len(sentences_a) if sentences_a else 0.0

    return {
        "mean_score": round(mean_score, 4),
        "max_score": round(max_score, 4),
        "matches": matched_sentences,
        "match_ratio": round(match_ratio, 4),
        "used_sbert": True,
    }


def is_sbert_available() -> bool:
    """Check whether the SBERT transformer layer is available."""
    return _SBERT_AVAILABLE
