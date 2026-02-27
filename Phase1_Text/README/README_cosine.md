# Cosine Similarity Module (Phase‑1)

## Overview
This module implements TF‑IDF based cosine similarity with lemmatization and n‑gram modeling to detect semantic similarity and paraphrased plagiarism.

## Files Included

### 1. cosine.py
Implements cosine similarity using the vector space model.

#### Functions:
- `lemmatize_text(text)`
  - Normalizes words using WordNet lemmatization.
- `cosine_sim(text1, text2)`
  - Converts text into TF‑IDF vectors
  - Uses unigrams and bigrams (n‑grams)
  - Computes cosine similarity score between 0 and 1

### 2. test_cosine.py
Unit tests for verifying semantic similarity detection.

Test cases include:
- Similar paraphrased text
- Completely unrelated text

## Algorithm Description
TF‑IDF converts documents into high‑dimensional vectors based on term importance. Cosine similarity measures the angle between vectors to determine similarity.

## Formula Used

Cosine Similarity:

(A · B) / (||A|| × ||B||)

Where:
- A and B are TF‑IDF vectors.

## Purpose in Project
Cosine similarity captures semantic similarity and paraphrased plagiarism, unlike Jaccard and LCS which rely on exact lexical overlap.

## Time and Space Complexity
- Time Complexity: O(V)
- Space Complexity: O(V)

Where V is the vocabulary size.

## Additional 
Cosine similarity in the vector space model captures topical and semantic similarity, complementing lexical similarity measures such as Jaccard and LCS.
