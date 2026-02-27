from Phase1_Text.preprocess.clean import clean_text
from Phase1_Text.preprocess.tokenizer import tokenize, remove_stopwords
from Phase1_Text.algorithms.jaccard import jaccard_similarity
from Phase1_Text.algorithms.lcs import lcs_similarity
from Phase1_Text.algorithms.cosine import cosine_sim
from Phase1_Text.scoring.aggregate import aggregate_text_score

def compare_texts(text1, text2):
    # Preprocess
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)

    tokens1 = remove_stopwords(tokenize(clean1))
    tokens2 = remove_stopwords(tokenize(clean2))

    # Algorithms
    j = jaccard_similarity(tokens1, tokens2)
    l = lcs_similarity(tokens1, tokens2)
    c = cosine_sim(clean1, clean2)

    # Aggregate
    final = aggregate_text_score(j, l, c)

    return {
    "jaccard": round(float(j), 4),
    "lcs": round(float(l), 4),
    "cosine": round(float(c), 4),
    "final_similarity": round(float(final), 4)
}
