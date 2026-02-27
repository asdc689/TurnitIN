# Jaccard Similarity Module (Phase‑1)

## Overview
This module implements Jaccard similarity, a set-based lexical similarity metric used to detect direct textual overlap in plagiarism detection.

## Files Included

### 1. jaccard.py
Contains the implementation of Jaccard similarity.

#### Function:
- `jaccard_similarity(tokens1, tokens2)`
  - Converts token lists to sets
  - Computes intersection and union
  - Returns similarity score between 0 and 1
  - Handles edge case of empty documents

### 2. test_jaccard.py
Unit tests for verifying correctness of the Jaccard similarity implementation.

Test cases include:
- Identical token lists
- Partial overlap
- No overlap
- Empty inputs

## Formula Used

Jaccard Similarity:

|A ∩ B| / |A ∪ B|

Where:
- A and B are sets of tokens from two documents.

## Purpose in Project
Jaccard similarity detects direct lexical overlap, making it effective for identifying copy‑paste plagiarism.

## Time and Space Complexity
- Time Complexity: O(n + m)
- Space Complexity: O(n + m)

Where n and m are the number of tokens in each document.

## Enhancement
Jaccard similarity is effective for detecting exact lexical overlap but does not capture word order or semantic similarity, hence it is combined with LCS and cosine similarity.
