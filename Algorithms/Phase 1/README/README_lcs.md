# LCS Similarity Module (Phase‑1)

## Overview
This module implements Longest Common Subsequence (LCS) based similarity using Dynamic Programming. LCS measures sequence-based similarity between two token lists.

## Files Included

### 1. lcs.py
Implements LCS similarity using a dynamic programming table.

#### Function:
- `lcs_similarity(a, b)`
  - Computes LCS length using DP
  - Normalizes the score by dividing by the minimum token length
  - Returns a similarity score between 0 and 1

### 2. test_lcs.py
Unit tests to validate correctness of LCS similarity.

Test cases include:
- Identical token sequences
- Partial subsequence matching
- Completely different sequences
- Reordered token sequences

## Algorithm Description
LCS finds the longest subsequence that appears in both sequences in the same order (not necessarily contiguous).

## Formula Used
Normalized LCS Score:

LCS(a, b) / min(len(a), len(b))

## Purpose in Project
LCS detects syntactic plagiarism where word order and structure are preserved but additional words may be inserted or removed.

## Time and Space Complexity
- Time Complexity: O(n × m)
- Space Complexity: O(n × m)

Where n and m are the number of tokens in each document.

## Enhancement 
LCS captures syntactic similarity and structural plagiarism but does not account for semantic similarity, which is handled separately by cosine similarity.