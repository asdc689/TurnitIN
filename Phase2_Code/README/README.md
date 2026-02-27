# Phase 2 – Code Plagiarism Detection Engine

## Overview
Phase‑2 focuses on detecting plagiarism in **source code**.  
The system supports **Python, C++, and Java** and is designed to handle:
- Same‑language plagiarism
- Cross‑language plagiarism (with documented limitations)

Unlike Phase‑1 (text plagiarism), this phase operates on **code structure and execution flow** rather than natural language.

---

## Supported Languages
- Python
- C++
- Java

Language detection is performed automatically at runtime.

---

## System Architecture

Input Code
→ Language Detection  
→ Code Preprocessing  
→ Similarity Algorithms  
→ Weighted Aggregation  
→ Plagiarism Report

---

## Preprocessing
### Code Cleaning
- Removes comments
- Normalizes whitespace
- Preserves structure‑critical tokens

### Tokenization
- Language‑specific tokenization
- Identifier normalization (variables → generic placeholders)

---

## Algorithms Used

### 1. Winnowing (Rabin‑Karp Fingerprinting)
- Detects exact or near‑exact code fragments
- Effective for same‑language comparisons
- Weak for cross‑language cases (expected behavior)

### 2. Code LCS (Longest Common Subsequence)
- Operates on token order
- Detects algorithmic similarity
- Primary signal for cross‑language plagiarism

### 3. AST Similarity (Tree‑Sitter)
- Structural similarity using AST node n‑grams
- Applied **only for same‑language comparisons**
- Disabled for cross‑language to avoid invalid matches

---

## Cross‑Language Handling (Important Design Choice)
AST structures differ across programming languages and cannot be directly compared.

Therefore:
- AST similarity is **disabled** for cross‑language comparisons
- Final score relies on LCS + Winnowing
- This avoids false positives and maintains academic correctness

---

## Score Aggregation

### Same‑Language
Final = 0.5 * Winnowing + 0.3 * LCS + 0.2 * AST

### Cross‑Language
Final = 0.7 * LCS + 0.3 * Winnowing (AST excluded)

---

## Output Report
The system outputs:
- Winnowing score
- LCS score
- AST score (None if cross‑language)
- Final similarity score

---

## Threshold Guidelines
- Same‑language ≥ 0.6 → Highly suspicious
- Cross‑language ≥ 0.45 → Suspicious

---

## Limitations
- No semantic (IR / CFG / PDG) comparison
- No ML or embedding‑based similarity
- Cross‑language scores are conservative by design

---

## Future Work
- Universal AST (UAST)
- Semantic graph comparison
- ML‑based embeddings
- Dataset‑level evaluation

---

## Status
✔ Phase‑2 Feature Complete  
✔ Ready for evaluation