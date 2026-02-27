from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))

def tokenize(text: str) -> list:
    return text.split()

def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in STOPWORDS]


