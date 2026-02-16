from algorithms.rabin_karp import similarity_score
from code_preprocess.language_tokenizer import normalize_identifiers

code1 = ["def", "var1", "(", ")", ":", "return", "var2", "+", "var3"]
code2 = ["def", "varA", "(", ")", ":", "return", "varB", "+", "varC"]
code3 = ["int", "main", "(", ")", "{", "return", "0", ";", "}"]

norm1 = normalize_identifiers(code1, lang="python")
norm2 = normalize_identifiers(code2, lang="python")
norm3 = normalize_identifiers(code3, lang="python")

print("Similar Code:", similarity_score(norm1, norm2))  # Expect high
print("Different Code:", similarity_score(norm1, norm3))  # Expect low