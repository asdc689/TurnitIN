"""
tfidf_similarity.py
-------------------
Document-level and sentence-level TF-IDF cosine similarity.

Roles in the engine:
  1. Document-level: Quick overall similarity signal. Catches paraphrasing
     that preserves domain-specific vocabulary (key terms survive even
     when sentence structure changes).
  2. Sentence-level: Cross-document sentence matching — finds which specific
     sentences are semantically close based on vocabulary overlap.
     This is the fallback for the SBERT semantic layer when the transformer
     model is not available.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def document_similarity(text_a: str, text_b: str) -> float:
    """
    Compute TF-IDF cosine similarity between two full document strings.

    Args:
        text_a: Normalized full text of document A
        text_b: Normalized full text of document B

    Returns:
        Float in [0.0, 1.0]
    """
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),   # unigrams + bigrams for richer signal
        min_df=1,
        sublinear_tf=True,    # apply log(1+tf) to dampen effect of very
                              # frequent terms
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(np.clip(score, 0.0, 1.0))
    except ValueError:
        # Happens if both texts are empty after vectorization
        return 0.0


def sentence_cross_similarity(sentences_a: list[str],
                               sentences_b: list[str]) -> dict:
    """
    For each sentence in document A, find the most similar sentence in
    document B using TF-IDF cosine similarity.

    Returns a dict with:
        'mean_score':     Average of best-match scores (overall semantic signal)
        'max_score':      Highest single-sentence match found
        'matches':        List of (sentence_a, best_match_in_b, score) tuples
                          for all pairs above the threshold
        'match_ratio':    Fraction of sentences in A that found a match above
                          threshold in B
    """
    MATCH_THRESHOLD = 0.55  # Tunable: lower = more matches flagged

    if not sentences_a or not sentences_b:
        return {
            "mean_score": 0.0,
            "max_score": 0.0,
            "matches": [],
            "match_ratio": 0.0,
        }

    # Fit vectorizer on the combined sentence pool
    all_sentences = sentences_a + sentences_b
    vectorizer = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(all_sentences)
    except ValueError:
        return {"mean_score": 0.0, "max_score": 0.0, "matches": [], "match_ratio": 0.0}

    n_a = len(sentences_a)
    vecs_a = tfidf_matrix[:n_a]
    vecs_b = tfidf_matrix[n_a:]

    # Full similarity matrix: shape (n_a, n_b)
    sim_matrix = cosine_similarity(vecs_a, vecs_b)

    best_scores = []
    matched_sentences = []

    for i, row in enumerate(sim_matrix):
        best_j = int(np.argmax(row))
        best_score = float(row[best_j])
        best_scores.append(best_score)

        if best_score >= MATCH_THRESHOLD:
            matched_sentences.append((
                sentences_a[i],
                sentences_b[best_j],
                round(best_score, 4),
            ))

    mean_score = float(np.mean(best_scores)) if best_scores else 0.0
    max_score = float(np.max(best_scores)) if best_scores else 0.0
    match_ratio = len(matched_sentences) / len(sentences_a) if sentences_a else 0.0

    return {
        "mean_score": round(mean_score, 4),
        "max_score": round(max_score, 4),
        "matches": matched_sentences,
        "match_ratio": round(match_ratio, 4),
    }
