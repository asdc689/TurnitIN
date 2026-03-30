"""
scorer.py
---------
Final scoring layer. Aggregates all similarity signals into a single
calibrated plagiarism score with a full diagnostic report.

SIGNAL STACK (7 signals total):
  ┌─────────────────────────────────────────────────────────────────┐
  │ Signal              │ Catches                                   │
  ├─────────────────────┼───────────────────────────────────────────┤
  │ Winnowing Jaccard   │ Exact/near-exact phrase matches           │
  │ TF-IDF (doc+sent)   │ Vocabulary overlap, light paraphrasing    │
  │ Semantic (SBERT)    │ Meaning-level paraphrasing, synonyms      │
  │ Fuzzy edit distance │ Minor word substitutions, character edits │
  │ Keyword Jaccard     │ Shared domain terms across heavy rewording│
  │ Char n-gram Jaccard │ Morphological similarity, root-word match │
  │ Numeric anchors     │ Preserved numbers, stats, measurements    │
  └─────────────────────┴───────────────────────────────────────────┘

TWO WEIGHT PROFILES:
  WITH SBERT:    Semantic layer is the dominant paraphrasing detector.
  WITHOUT SBERT: Keyword + char n-gram + fuzzy are promoted to compensate.
"""

from Phase1_Text.preprocess.preprocessor import preprocess
from Phase1_Text.algorithms.winnowing import fingerprint, winnowing_similarity, get_matched_kgrams
from Phase1_Text.algorithms.tfidf_similarity import document_similarity, sentence_cross_similarity
from Phase1_Text.algorithms.fuzzy_matcher import fuzzy_sentence_matches
from Phase1_Text.algorithms.section_analyzer import section_similarity_report
from Phase1_Text.algorithms.semantic_similarity import semantic_sentence_similarity, is_sbert_available
from Phase1_Text.algorithms.keyword_analysis import run_all_keyword_signals
from Phase1_Text.algorithms.synonym_normalizer import synonym_combined_score


# ── Weight Profiles ───────────────────────────────────────────────────────────
# FIX: Weights must sum to exactly 1.0. Original NO_SBERT summed to 1.01.
# Also renamed "semantic" key in NO_SBERT profile to clarify it is TF-IDF fallback,
# and redistributed synonym's 0.00 in WITH_SBERT into winnowing for cleaner accounting.
WEIGHTS_WITH_SBERT = {
    "winnowing":  0.20,
    "semantic":   0.60,    # SBERT dominates paraphrase detection
    "tfidf":      0.10,
    "fuzzy":      0.05,
    "keyword":    0.05,
    "synonym":    0.00,    # SBERT already handles this; weight is zero
}

WEIGHTS_NO_SBERT = {
    "winnowing":  0.04,
    "semantic":   0.02,    # TF-IDF fallback — low weight, poor at paraphrasing
    "tfidf":      0.04,
    "fuzzy":      0.10,    # edit-distance: catches structural near-matches
    "keyword":    0.05,    # char n-gram + numeric anchors
    "synonym":    0.75,    # synonym-aware Jaccard/containment — primary signal
}

# Sanity-check at import time — catches future accidental weight drift
assert abs(sum(WEIGHTS_WITH_SBERT.values()) - 1.0) < 1e-9, \
    f"WEIGHTS_WITH_SBERT must sum to 1.0, got {sum(WEIGHTS_WITH_SBERT.values())}"
assert abs(sum(WEIGHTS_NO_SBERT.values()) - 1.0) < 1e-9, \
    f"WEIGHTS_NO_SBERT must sum to 1.0, got {sum(WEIGHTS_NO_SBERT.values())}"

HOTSPOT_THRESHOLD = 0.65
HOTSPOT_BOOST_FACTOR = 0.15


def _interpret_score(score: float) -> dict:
    if score >= 0.80:
        return {"level": "CRITICAL", "verdict": "Almost certainly plagiarized"}
    elif score >= 0.60:
        return {"level": "HIGH",     "verdict": "Strong indicators of plagiarism"}
    elif score >= 0.40:
        return {"level": "MEDIUM",   "verdict": "Significant similarity — review recommended"}
    elif score >= 0.20:
        return {"level": "LOW",      "verdict": "Some similarity detected — likely coincidental"}
    else:
        return {"level": "MINIMAL",  "verdict": "No significant plagiarism detected"}


def compute_similarity(text_a: str, text_b: str,
                        file_a_name: str = "Document A",
                        file_b_name: str = "Document B") -> dict:
    """
    Run the full text plagiarism analysis pipeline on two text strings.
    """
    # ── Guard: empty documents ────────────────────────────────────────────────
    if not text_a.strip() or not text_b.strip():
        return _empty_report(file_a_name, file_b_name)

    # ── Preprocessing ─────────────────────────────────────────────────────────
    print("[Engine] Preprocessing documents...")
    data_a = preprocess(text_a)
    data_b = preprocess(text_b)

    stemming_active = data_a.get("lemma_active", False)
    # Use stemmed tokens for signals that benefit from inflection collapsing.
    # Use raw tokens for fuzzy matching (stemming hurts edit-distance accuracy).
    tokens_a = data_a["lemmatized_tokens"] if stemming_active else data_a["tokens"]
    tokens_b = data_b["lemmatized_tokens"] if stemming_active else data_b["tokens"]

    # ── Signal 1: Winnowing ───────────────────────────────────────────────────
    print("[Engine] Running Winnowing fingerprinting...")
    fp_a = fingerprint(tokens_a)
    fp_b = fingerprint(tokens_b)
    winnowing_score = winnowing_similarity(fp_a, fp_b)
    matched_kgrams = get_matched_kgrams(tokens_a, tokens_b)

    # ── Signal 2: TF-IDF ─────────────────────────────────────────────────────
    print("[Engine] Running TF-IDF similarity...")
    tfidf_doc_score = document_similarity(
        data_a["normalized_text"], data_b["normalized_text"]
    )
    tfidf_sentence_result = sentence_cross_similarity(
        data_a["sentences"], data_b["sentences"]
    )
    tfidf_combined = (tfidf_doc_score * 0.4) + (tfidf_sentence_result["mean_score"] * 0.6)

    # ── Signal 3: Semantic ────────────────────────────────────────────────────
    sbert_active = is_sbert_available()
    print(f"[Engine] Running semantic similarity "
          f"(SBERT={'YES' if sbert_active else 'NO — TF-IDF fallback'})...")
    semantic_result = semantic_sentence_similarity(
        data_a["sentences"], data_b["sentences"]
    )
    semantic_score = semantic_result["mean_score"]

    # ── Signal 4: Fuzzy ───────────────────────────────────────────────────────
    print("[Engine] Running fuzzy sentence matching...")
    fuzzy_result = fuzzy_sentence_matches(
        data_a["sentences"], data_b["sentences"]
    )
    fuzzy_score = fuzzy_result["mean_score"]

    # ── Signals 5+6+7: Keyword / Char N-gram / Numeric ───────────────────────
    print("[Engine] Running keyword + char n-gram + numeric analysis...")
    kw_results = run_all_keyword_signals(
        data_a["normalized_text"], data_b["normalized_text"],
        tokens_a, tokens_b   # stemmed tokens — better inflection coverage
    )
    keyword_combined = kw_results["combined"]

    # ── Signal 8: Synonym-Aware Semantic (no SBERT required) ─────────────────
    print("[Engine] Running synonym-aware keyword similarity...")
    syn_score = synonym_combined_score(tokens_a, tokens_b)  # stemmed tokens

    # ── Section Hotspot ───────────────────────────────────────────────────────
    print("[Engine] Running section-level hotspot analysis...")
    section_report = section_similarity_report(text_a, text_b)
    max_section_score = section_report["max_section_score"]

    # ── Final Score ───────────────────────────────────────────────────────────
    W = WEIGHTS_WITH_SBERT if sbert_active else WEIGHTS_NO_SBERT

    base_score = (
        W["winnowing"] * winnowing_score  +
        W["semantic"]  * semantic_score   +
        W["tfidf"]     * tfidf_combined   +
        W["fuzzy"]     * fuzzy_score      +
        W["keyword"]   * keyword_combined +
        W["synonym"]   * syn_score
    )

    hotspot_boost = 0.0
    if max_section_score >= HOTSPOT_THRESHOLD:
        hotspot_boost = HOTSPOT_BOOST_FACTOR * (
            (max_section_score - HOTSPOT_THRESHOLD) / (1.0 - HOTSPOT_THRESHOLD)
        )

    final_score = min(base_score + hotspot_boost, 1.0)
    final_score = round(final_score, 4)
    interpretation = _interpret_score(final_score)

    # ── Paraphrase Suspicion Detection ────────────────────────────────────────
    # Signature of synonym-based paraphrasing (without SBERT):
    #   - Winnowing is very low (no n-gram matches) OR zero
    #   - But Fuzzy is notably above baseline (sentence structure preserved)
    #   - And TF-IDF shows some vocabulary overlap
    # This pattern means the documents are probably related but fully reworded.
    # We can't score it high without SBERT, but we can flag it for review.
    paraphrase_suspected = (
        not sbert_active
        and winnowing_score < 0.05
        and fuzzy_score > 0.25
        and tfidf_doc_score > 0.12          # raised from 0.08 to avoid short-sentence false positives
        and len(data_a["sentences"]) >= 2   # need at least 2 sentences to be meaningful
    )
    if paraphrase_suspected:
        interpretation["verdict"] += (
            " | ⚠ Paraphrase pattern detected — install sentence-transformers for full analysis"
        )

    # Deduplicate sentence matches across the three signal layers.
    # The same (sent_a, sent_b) pair can fire in tfidf, fuzzy, and semantic
    # independently. Keep the highest-scoring occurrence of each unique pair.
    _seen: dict[tuple, float] = {}
    for sent_a, sent_b, score in (
        tfidf_sentence_result["matches"]
        + fuzzy_result["matches"]
        + semantic_result.get("matches", [])
    ):
        key = (sent_a.strip(), sent_b.strip())
        if key not in _seen or score > _seen[key]:
            _seen[key] = score
    deduped_matches = [
        (a, b, s) for (a, b), s in sorted(_seen.items(), key=lambda x: -x[1])
    ]

    report = {
        "summary": {
            "file_a":          file_a_name,
            "file_b":          file_b_name,
            "final_score":     final_score,
            "final_score_pct": f"{final_score * 100:.1f}%",
            "risk_level":      interpretation["level"],
            "verdict":         interpretation["verdict"],
            "sbert_used":      sbert_active,
            "lemma_active": stemming_active,
            "paraphrase_suspected": paraphrase_suspected,
            # Expose length ratio so callers can warn when comparing
            # documents of very different sizes.
            "length_ratio":    round(
                min(len(data_a["tokens"]), len(data_b["tokens"])) /
                max(len(data_a["tokens"]), len(data_b["tokens"]), 1),
                4
            ),
        },
        "signal_breakdown": {
            "winnowing_jaccard":       round(winnowing_score, 4),
            "tfidf_document":          round(tfidf_doc_score, 4),
            "tfidf_sentence_mean":     tfidf_sentence_result["mean_score"],
            "semantic_sentence_mean":  round(semantic_score, 4),
            "fuzzy_sentence_mean":     round(fuzzy_score, 4),
            "keyword_jaccard":         kw_results["keyword_jaccard"],
            "char_ngram_jaccard":      kw_results["char_ngram"],
            "numeric_anchor":          kw_results["numeric_anchor"],
            "keyword_combined":        kw_results["combined"],
            "synonym_score":           round(syn_score, 4),
            "max_section_score":       round(max_section_score, 4),
            "hotspot_boost_applied":   round(hotspot_boost, 4),
            "weight_profile":          "WITH_SBERT" if sbert_active else "NO_SBERT",
        },
        "matched_content": {
            "matched_phrases":       matched_kgrams[:20],
            "total_matched_phrases": len(matched_kgrams),
            "sentence_matches":      deduped_matches[:15],
            "high_risk_sections":    section_report["high_risk_pairs"],
            "hotspot_text":          section_report["hotspot_text"],
        },
        "document_stats": {
            "tokens_a":    len(data_a["tokens"]),
            "tokens_b":    len(data_b["tokens"]),
            "sentences_a": len(data_a["sentences"]),
            "sentences_b": len(data_b["sentences"]),
        },
    }
    return report


def _empty_report(file_a_name: str, file_b_name: str) -> dict:
    return {
        "summary": {
            "file_a": file_a_name, "file_b": file_b_name,
            "final_score": 0.0, "final_score_pct": "0.0%",
            "risk_level": "MINIMAL",
            "verdict": "One or both documents are empty",
            "sbert_used": False,
        },
        "signal_breakdown": {
            "winnowing_jaccard": 0.0, "tfidf_document": 0.0,
            "tfidf_sentence_mean": 0.0, "semantic_sentence_mean": 0.0,
            "fuzzy_sentence_mean": 0.0, "keyword_jaccard": 0.0,
            "char_ngram_jaccard": 0.0, "numeric_anchor": 0.0,
            "keyword_combined": 0.0, "synonym_score": 0.0,
            "max_section_score": 0.0,
            "hotspot_boost_applied": 0.0, "weight_profile": "N/A",
        },
        "matched_content": {
            "matched_phrases": [], "total_matched_phrases": 0,
            "sentence_matches": [], "high_risk_sections": [],
            "hotspot_text": None,
        },
        "document_stats": {"tokens_a": 0, "tokens_b": 0, "sentences_a": 0, "sentences_b": 0},
    }


def format_report(report: dict) -> str:
    s  = report["summary"]
    sb = report["signal_breakdown"]
    mc = report["matched_content"]
    ds = report["document_stats"]
    sbert_tag = "[SBERT]" if s["sbert_used"] else "[TF-IDF fallback]"
    stem_tag  = "[Lemmatization]" if s.get("lemma_active") else "[no lemmatization — install nltk]"

    lines = [
        "=" * 66,
        "  PLAGIARISM ANALYSIS REPORT",
        "=" * 66,
        f"  File A : {s['file_a']}",
        f"  File B : {s['file_b']}",
        "-" * 66,
        f"  FINAL SCORE  :  {s['final_score_pct']}",
        f"  RISK LEVEL   :  {s['risk_level']}",
        f"  VERDICT      :  {s['verdict']}",
    ]

    # FIX: Warn when documents differ greatly in length — scores can be misleading
    length_ratio = s.get("length_ratio", 1.0)
    if length_ratio < 0.3:
        lines.append(
            f"  ⚠ LENGTH WARNING : Documents differ significantly in size "
            f"(ratio={length_ratio:.2f}). Jaccard scores may understate similarity."
        )

    lines += [
        "-" * 66,
        "  SIGNAL BREAKDOWN",
        f"  Winnowing (fingerprint match)    : {sb['winnowing_jaccard']:.2%}  {stem_tag}",
        f"  TF-IDF document similarity       : {sb['tfidf_document']:.2%}",
        f"  TF-IDF sentence mean             : {sb['tfidf_sentence_mean']:.2%}",
        f"  Semantic similarity (mean)       : {sb['semantic_sentence_mean']:.2%}  {sbert_tag}",
        f"  Fuzzy edit-distance (mean)       : {sb['fuzzy_sentence_mean']:.2%}",
        f"  Keyword Jaccard (content words)  : {sb['keyword_jaccard']:.2%}",
        f"  Char n-gram Jaccard              : {sb['char_ngram_jaccard']:.2%}",
        f"  Numeric anchor match             : {sb['numeric_anchor']:.2%}",
        f"  Synonym-aware score              : {sb['synonym_score']:.2%}",
        f"  Max section score                : {sb['max_section_score']:.2%}",
        f"  Hotspot boost                    : +{sb['hotspot_boost_applied']:.2%}",
        f"  Weight profile                   : {sb['weight_profile']}",
        "-" * 66,
        "  DOCUMENT STATS",
        f"  Tokens    — A: {ds['tokens_a']:,}   B: {ds['tokens_b']:,}",
        f"  Sentences — A: {ds['sentences_a']:,}   B: {ds['sentences_b']:,}",
        "-" * 66,
    ]

    if mc["matched_phrases"]:
        lines.append("  TOP MATCHED PHRASES (Winnowing)")
        for phrase in mc["matched_phrases"][:10]:
            lines.append(f"    • \"{phrase}\"")
        if mc["total_matched_phrases"] > 10:
            lines.append(f"    ... and {mc['total_matched_phrases'] - 10} more")
        lines.append("")

    if mc["hotspot_text"]:
        h = mc["hotspot_text"]
        lines += [
            f"  HIGHEST-RISK SECTION  (score: {h['score']:.2%})",
            "  ── Document A ──",
            f"  {h['section_a'][:300]}{'...' if len(h['section_a']) > 300 else ''}",
            "  ── Document B ──",
            f"  {h['section_b'][:300]}{'...' if len(h['section_b']) > 300 else ''}",
        ]

    lines.append("=" * 66)
    return "\n".join(lines)
