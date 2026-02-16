# Text Plagiarism Detection System (Phase‑1)

## Overview
This project implements a classical text plagiarism detection system using multiple similarity algorithms and weighted aggregation. The system detects lexical, syntactic, and semantic similarity between documents.

## Folder Structure

project_root/
│
├── preprocess/
│   ├── clean.py
│   ├── tokenizer.py
│   └── __init__.py
│
├── algorithms/
│   ├── jaccard.py
│   ├── lcs.py
│   ├── cosine.py
│   └── __init__.py
│
├── scoring/
│   ├── aggregate.py
│   └── __init__.py
│
├── engine/
│   ├── text_similarity.py
│   └── __init__.py
│
├── tests/
│   ├── test_preprocess.py
│   ├── test_jaccard.py
│   ├── test_lcs.py
│   └── test_cosine.py
│
├── main.py
└── README.md

## Note on __init__.py Files

Each module directory (preprocess, algorithms, scoring, engine) contains an `__init__.py` file.  
This file marks the directory as a Python package, enabling modular imports such as:

```Python
from algorithms.jaccard import jaccard_similarity
```

## How to Run :

### Install Dependencies
pip install nltk scikit-learn

### Run Preprocessing Tests
python -m tests.test_preprocess

### Run Similarity Engine
python main.py

## Example Output

--- Plagiarism Report ---
jaccard: 0.53  
lcs: 0.55  
cosine: 0.41  
final_similarity: 0.49  

## Algorithms Used
- Jaccard Similarity (Lexical overlap)
- Longest Common Subsequence (Structural similarity)
- TF‑IDF Cosine Similarity (Semantic similarity)
- Weighted Aggregation

## Phase‑1 Outcome
A fully functional textual plagiarism detection system with modular architecture and unit testing.
