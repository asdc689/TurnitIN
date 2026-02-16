# Preprocessing Module (Phase‑1)

## Overview
This module performs text preprocessing for the plagiarism detection system. Preprocessing is required to normalize text before similarity algorithms are applied.

## Files Included :

### 1. clean.py
This file contains functions to clean raw text.

#### Functions:
- `normalize_whitespace(text)`: Removes extra spaces.
- `clean_text(text)`: 
  - Converts text to lowercase
  - Removes punctuation and special characters
  - Preserves apostrophes
  - Normalizes whitespace

### 2. tokenizer.py
This file performs tokenization and stopword removal.

#### Functions:
- `tokenize(text)`: Splits cleaned text into tokens (words).
- `remove_stopwords(tokens)`: Removes common English stopwords using NLTK.

### 3. test_preprocess.py
This file tests the preprocessing pipeline by printing raw text, cleaned text, tokens, and filtered tokens.

## Working Pipeline

Raw Text → Cleaning → Tokenization → Stopword Removal

## Purpose in Project
Preprocessing significantly reduces noise in textual data and improves the accuracy of lexical similarity algorithms such as Jaccard and LCS.

## Technologies Used
- Python
- Regular Expressions (re)
- NLTK stopwords corpus

## Output Example

RAW: This is a Sample text, for Testing!!!  
CLEANED: this is a sample text for testing  
TOKENS: ['this', 'is', 'a', 'sample', 'text', 'for', 'testing']  
FINAL TOKENS: ['sample', 'text', 'testing']
