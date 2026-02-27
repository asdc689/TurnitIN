## Problem Statement :
Plagiarism in textual content is a major academic issue. Manual detection is inefficient and unreliable. This project aims to design a system that automatically detects plagiarism using classical algorithmic and NLP techniques.

## Objectives :
1) To preprocess textual documents for similarity analysis
2) To implement multiple similarity detection algorithms
3) To aggregate similarity scores for robust plagiarism detection
4) To build a modular and testable plagiarism detection engine

## Methodology :
The system preprocesses text using cleaning, tokenization, and stopword removal. Three similarity algorithms are applied: Jaccard similarity for lexical overlap, LCS for structural similarity, and TF‑IDF cosine similarity for semantic similarity. The results are combined using weighted aggregation to produce a final plagiarism score.

## Algorithms Used :
| Algorithm                        | Purpose                                     |
| -------------------------------- | ------------------------------------------- |
| Jaccard Similarity               | Detects exact word overlap                  |
| Longest Common Subsequence (LCS) | Detects sequence and structural similarity  |
| TF‑IDF Cosine Similarity         | Detects semantic and paraphrased similarity |
| Weighted Aggregation             | Combines all scores                         |

## Results :
The system successfully detects:
- Copy‑paste plagiarism
- Sentence reordering plagiarism
- Paraphrased plagiarism

## Conclusion :
A modular plagiarism detection system was developed using classical DSA and NLP techniques. The system demonstrates effective detection of lexical, syntactic, and semantic similarity, providing a foundation for advanced plagiarism detection systems.

## System Architecture Diagram :

Input Text
   ↓
Text Cleaning (lowercase, punctuation removal)
   ↓
Tokenization
   ↓
Stopword Removal
   ↓
Jaccard Similarity (Lexical Overlap)
   ↓
LCS Similarity (Sequence Structure)
   ↓
TF‑IDF Cosine Similarity (Semantic Topic)
   ↓
Weighted Aggregation Engine
   ↓
Final Plagiarism Similarity Score
