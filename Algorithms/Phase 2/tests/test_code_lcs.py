from algorithms.code_lcs import lcs_similarity

# Same logic, different variable names
code1 = ["def", "var1", "(", ")", ":", "return", "var2", "+", "var3"]
code2 = ["def", "varA", "(", ")", ":", "return", "varB", "+", "varC"]

# Reordered logic
code3 = ["return", "var2", "+", "var3", "def", "var1", "(", ")", ":"]

# Completely different
code4 = ["int", "main", "(", ")", "{", "return", "0", ";", "}"]

print("Similar Code:", lcs_similarity(code1, code2))      # Expect ~1.0
print("Reordered Code:", lcs_similarity(code1, code3))   # Expect ~0.5–0.7
print("Different Code:", lcs_similarity(code1, code4))   # Expect ~0.0
