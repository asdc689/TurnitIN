# Code Preprocessing and Tokenization Module (Phase‑2)

## Overview
This module preprocesses source code to enable code plagiarism detection. It removes comments, normalizes whitespace, tokenizes code, and normalizes variable names.

## Files Included

### 1. clean_code.py
Removes single-line and multi-line comments and normalizes whitespace.

### 2. language_tokenizer.py
Tokenizes source code into keywords, identifiers, operators, and literals. Identifiers are normalized to generic variable names (var1, var2, ...).

### 3. test_code_preprocess.py
Unit tests for preprocessing and tokenization.

## Processing Pipeline
Raw Code → Comment Removal → Whitespace Normalization  
→ Tokenization → Identifier Normalization

## Purpose in Project
This module ensures that code similarity detection focuses on logic rather than formatting or variable naming differences.