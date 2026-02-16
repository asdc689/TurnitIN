# Code LCS Similarity Module (Phase‑2)

## Overview
This module implements Longest Common Subsequence (LCS) on normalized code tokens to detect structural similarity between programs.

## Why Code LCS is Needed
Fingerprinting (Rabin–Karp + Winnowing) detects copied fragments.
Code LCS detects:
- Reordered statements
- Refactored logic
- Partial copying

Together, they form a robust code plagiarism detector.

## Files Included

### code_lcs.py
Implements token-based LCS and normalized similarity scoring.

### test_code_lcs.py
Test cases for similar, reordered, and different code structures.

## Algorithm Pipeline

Normalized Code Tokens
→ Dynamic Programming (LCS)
→ Normalized Similarity Score

## Formula
LCS Similarity = LCS_length / min(len(code1), len(code2))

## Advantages
- Detects logical similarity
- Independent of variable names
- Resistant to formatting changes

## Time Complexity
O(n × m) where n and m are token lengths.
Used after fingerprinting to reduce computational cost.
