from code_preprocess.clean_code import clean_code
from code_preprocess.code_tokenizer import tokenize_code, normalize_identifiers

code = """
# Sum function
def sum(a, b):
    result = a + b
    return result
"""

cleaned = clean_code(code)
tokens = tokenize_code(cleaned)
normalized = normalize_identifiers(tokens)

print("CLEANED CODE:", cleaned)
print("TOKENS:", tokens)
print("NORMALIZED TOKENS:", normalized)
