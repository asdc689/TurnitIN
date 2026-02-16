from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

def lemmatize_text(text):
    return " ".join(lemmatizer.lemmatize(w) for w in text.split())

def cosine_sim(text1, text2):
    text1 = lemmatize_text(text1.lower())
    text2 = lemmatize_text(text2.lower())

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2)
    )

    vectors = vectorizer.fit_transform([text1, text2])
    return cosine_similarity(vectors[0], vectors[1])[0][0]


if __name__ == "__main__":
    t1 = "plagiarism detection system compares documents"
    t2 = "document similarity System detects PlagiARISM"

    print("Cosine Similarity:", cosine_sim(t1, t2))

# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

# def cosine_sim(text1, text2):
#     vectorizer = TfidfVectorizer(
#         lowercase=True,
#         stop_words='english',
#         ngram_range=(1, 2)
#     )
    
#     vectors = vectorizer.fit_transform([text1, text2])
#     return cosine_similarity(vectors[0], vectors[1])[0][0]


