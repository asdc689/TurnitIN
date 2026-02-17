# Rabin–Karp Fingerprinting Module with Winnowing (Phase‑2)

## Overview
This module implements Rabin–Karp rolling hash combined with the Winnowing algorithm to detect code plagiarism efficiently and robustly.

## Why Winnowing is Used
Plain Rabin–Karp generates many fingerprints, which may include noise.
Winnowing selects representative fingerprints by choosing the minimum hash
value within a sliding window, a technique used in real plagiarism detection systems like Turnitin.

## Files Included

### rabin_karp.py
Implements Rabin-Karp with stable cryptographic hashing and token normalization to ensure deterministic fingerprint-based code plagiarism detection. 
- Stable MD5-based hashing (deterministic)
- k-gram rolling hash fingerprint generation
- Winnowing-based fingerprint selection
- Jaccard similarity over selected fingerprints

### test_rabin_karp.py
- Tests for similar and dissimilar code fragments

## Algorithm Description
Rabin-Karp uses rolling hash to compute hash values for k-length token sequences (k-grams). Fingerprints are compared using Jaccard similarity.

## Algorithm Pipeline
Tokenized & Normalized Code
→ k-gram Fingerprinting (Rabin–Karp)
→ Winnowing (Noise Reduction)
→ Jaccard Similarity
→ Code Similarity Score

## Parameters
- k = 3 (k-gram size, suitable for small/medium code)
- window_size = 4 (winnowing window)

## Advantages
- Resistant to variable renaming
- Resistant to formatting changes
- Reduced false positives
- Deterministic and reproducible

## Purpose in Project
This module detects copied code blocks even after variable renaming and formatting changes.

## Time Complexity
O(n) for fingerprint generation and selection.

## Note :
Python’s built-in hash() is not used because it is non-deterministic. 
A stable MD5-based hashing function is used to ensure consistent fingerprints.
