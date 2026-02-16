# AST-Based Code Similarity Module (Phase‑2)

## Overview
This module implements Abstract Syntax Tree (AST) based similarity detection for Python source code. Unlike token-based approaches, AST similarity focuses on program structure and logic.

## Why AST Similarity is Important
AST-based analysis detects plagiarism even when:
- Variable names are changed
- Code is refactored
- Formatting is altered
- Statements are rewritten logically

This makes it the most robust plagiarism detection method in the system.

## Files Included

### ast_similarity.py
- Parses Python code into AST
- Extracts AST node types
- Computes similarity using Jaccard similarity

### test_ast_similarity.py
- Test cases for similar, modified, and different code structures

## Algorithm Pipeline

Raw Python Code
→ AST Parsing
→ AST Node Extraction
→ Set-Based Similarity
→ AST Similarity Score

## Formula
AST Similarity = |Common AST Nodes| / |Total Unique AST Nodes|

## Advantages
- Logic-level plagiarism detection
- Independent of variable names
- Resistant to formatting changes
- Complements token-based methods

## Limitations
- Language-specific (Python only)
- Cannot detect semantic equivalence with different control flow

## Time Complexity
O(n) where n is the number of AST nodes.
