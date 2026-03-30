"""
section_analyzer.py
-------------------
Breaks documents into sections (paragraphs) and runs multiple similarity
signals on each section independently.

WHY THIS EXISTS:
  A document-level similarity score of 20% might hide the fact that one
  specific paragraph is 90% plagiarized. Without section analysis, a
  student could copy one complete section and pad the rest with original
  writing — the overall score gets diluted and the plagiarism goes undetected.

CHANGE vs original:
  Original only ran Winnowing on sections — so paraphrased sections with
  zero n-gram overlap always scored 0% even when clearly plagiarized.

  Now runs THREE signals per section pair and fuses them:
    1. Winnowing Jaccard       — catches exact/near-exact phrase copying
    2. TF-IDF cosine           — catches vocabulary overlap / light paraphrasing
    3. Synonym-aware Jaccard   — catches synonym substitution within sections

  The fused score is max(winnowing, tfidf, synonym) rather than a weighted
  average, because in section analysis we want to flag ANY strong signal,
  not require all signals to fire simultaneously.
"""

import re

from Phase1_Text.preprocess.preprocessor import preprocess, split_into_sentences
from Phase1_Text.algorithms.winnowing import fingerprint, winnowing_similarity
from Phase1_Text.algorithms.tfidf_similarity import document_similarity
from Phase1_Text.algorithms.synonym_normalizer import synonym_combined_score

# Maximum sections compared per document. Caps the O(n²) pairwise comparison
# to at most MAX_SECTIONS² pairs. At 60×60 = 3,600 pairs this is fast even
# for large documents; the most suspicious sections are sampled by length
# (longer sections carry more signal than 3-sentence micro-windows).
MAX_SECTIONS = 60


def split_into_sections(text: str) -> list[str]:
    """
    Split text into sections by double newline (paragraph breaks).
    Falls back to fixed-size sentence windows if no paragraph breaks found.
    """
    sections = re.split(r"\n\s*\n", text.strip())
    sections = [s.strip() for s in sections if s.strip()]

    if len(sections) <= 1:
        sentences = split_into_sentences(text)
        window_size = 3
        sections = []
        for i in range(0, len(sentences), window_size):
            chunk = " ".join(sentences[i:i + window_size])
            if chunk.strip():
                sections.append(chunk)

    return sections


def _section_fused_score(sec_a: str, sec_b: str,
                          fp_a: set, fp_b: set,
                          tokens_a: list, tokens_b: list) -> float:
    """
    Compute a fused similarity score for a section pair using three signals.

    Uses max() so that ANY strong signal flags the section — a paraphrased
    section may score 0 on Winnowing but high on TF-IDF or synonym.

    Returns float in [0.0, 1.0].
    """
    # Signal 1: Winnowing (exact n-gram overlap)
    win_score = winnowing_similarity(fp_a, fp_b)

    # Signal 2: TF-IDF document cosine (vocabulary overlap)
    norm_a = " ".join(tokens_a)
    norm_b = " ".join(tokens_b)
    tfidf_score = document_similarity(norm_a, norm_b) if norm_a and norm_b else 0.0

    # Signal 3: Synonym-aware Jaccard (catches synonym substitution)
    syn_score = synonym_combined_score(tokens_a, tokens_b)

    # Fuse: take the maximum — any strong signal should flag the section
    return round(max(win_score, tfidf_score, syn_score), 4)


def section_similarity_report(text_a: str, text_b: str) -> dict:
    """
    Compute per-section fused similarity between two documents.

    Runs every section of document A against every section of document B
    and finds the highest-similarity pairings.

    Returns:
        'section_scores':    List of (section_a_idx, section_b_idx, score)
                             sorted by score descending
        'max_section_score': The highest fused similarity found between any two sections
        'high_risk_pairs':   Section pairs with fused similarity > 0.7
        'hotspot_text':      The actual text of the highest-risk section pair
    """
    HIGH_RISK_THRESHOLD = 0.7

    sections_a = split_into_sections(text_a)
    sections_b = split_into_sections(text_b)

    if not sections_a or not sections_b:
        return {
            "section_scores":    [],
            "max_section_score": 0.0,
            "high_risk_pairs":   [],
            "hotspot_text":      None,
        }

    # Cap to MAX_SECTIONS per document. Sample by descending length so the
    # most content-rich sections are always included — short 3-sentence windows
    # produced by the fallback splitter are deprioritised naturally.
    if len(sections_a) > MAX_SECTIONS:
        sections_a = sorted(sections_a, key=len, reverse=True)[:MAX_SECTIONS]
    if len(sections_b) > MAX_SECTIONS:
        sections_b = sorted(sections_b, key=len, reverse=True)[:MAX_SECTIONS]

    # Precompute fingerprints and tokens for all sections
    processed_a = []
    for sec in sections_a:
        data = preprocess(sec)
        tokens = data.get("lemmatized_tokens") or data["tokens"]
        processed_a.append((fingerprint(tokens), tokens))

    processed_b = []
    for sec in sections_b:
        data = preprocess(sec)
        tokens = data.get("lemmatized_tokens") or data["tokens"]
        processed_b.append((fingerprint(tokens), tokens))

    # Compare all pairs with fused scoring
    all_scores = []
    for i, (fp_a, tok_a) in enumerate(processed_a):
        for j, (fp_b, tok_b) in enumerate(processed_b):
            score = _section_fused_score(
                sections_a[i], sections_b[j], fp_a, fp_b, tok_a, tok_b
            )
            all_scores.append((i, j, score))

    all_scores.sort(key=lambda x: x[2], reverse=True)

    high_risk = [(i, j, s) for i, j, s in all_scores if s >= HIGH_RISK_THRESHOLD]

    hotspot_text = None
    if all_scores:
        best_i, best_j, _ = all_scores[0]
        hotspot_text = {
            "section_a": sections_a[best_i],
            "section_b": sections_b[best_j],
            "score":     all_scores[0][2],
        }

    return {
        "section_scores":    all_scores[:20],
        "max_section_score": all_scores[0][2] if all_scores else 0.0,
        "high_risk_pairs":   high_risk,
        "hotspot_text":      hotspot_text,
    }
