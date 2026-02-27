# Aggregation and Text Similarity Engine (Phase‑1)

## Overview
This module implements the aggregation and the orchestration engine that integrates preprocessing and all similarity algorithms. Weighted score fusion was applied to generate a final plagiarism similarity score. A command line interface was developed for system demonstration.

## Files Included

### 1. aggregate.py
Implements weighted aggregation of similarity scores.

#### Function:
- `aggregate_text_score(jaccard, lcs, cosine)`
  - Combines scores using weighted fusion.
  - Weights used: Jaccard (0.2), LCS (0.2), Cosine (0.6).

### 2. engine/text_similarity.py
Orchestrates the full plagiarism detection pipeline.

#### Function:
- `compare_texts(text1, text2)`
  - Performs preprocessing
  - Runs Jaccard, LCS, and Cosine similarity
  - Aggregates results
  - Returns JSON-like dictionary output

### 3. main.py
Command-line interface to run plagiarism detection interactively.

## System Pipeline

Input Text → Cleaning → Tokenization → Stopword Removal  
→ Jaccard Similarity  
→ LCS Similarity  
→ Cosine Similarity  
→ Weighted Aggregation  
→ Final Plagiarism Score

## Purpose in Project
This module integrates all components into a functional plagiarism detection engine and provides a user interface for demonstration.

## Additional 
Weighted aggregation improves robustness by combining lexical, syntactic, and semantic similarity measures, reducing false positives and false negatives.


