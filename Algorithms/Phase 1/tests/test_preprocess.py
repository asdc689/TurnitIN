from preprocess.clean import clean_text
from preprocess.tokenizer import tokenize, remove_stopwords

text = "This is a Sample text, for Testing!!!"

cleaned = clean_text(text)
tokens = tokenize(cleaned)
final = remove_stopwords(tokens)

print("RAW:", text)
print("CLEANED:", cleaned)
print("TOKENS:", tokens)
print("FINAL TOKENS:", final)
