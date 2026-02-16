from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))

def tokenize(text: str) -> list:
    return text.split()

def remove_stopwords(tokens: list) -> list:
    return [t for t in tokens if t not in STOPWORDS]


if __name__ == "__main__":
    from clean import clean_text
    
    sample = "This is a Sample text for Testing plagiarism detection."
    
    cleaned = clean_text(sample)
    tokens = tokenize(cleaned)
    filtered = remove_stopwords(tokens)
    
    print("CLEANED:", cleaned)
    print("TOKENS:", tokens)
    print("FILTERED:", filtered)
