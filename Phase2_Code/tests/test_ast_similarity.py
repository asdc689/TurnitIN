from algorithms.ast_similarity import ast_similarity

code1 = """
def add(a, b):
    return a + b
"""

code2 = """
def sum(x, y):
    result = x + y
    return result
"""

code3 = """
def multiply(a, b):
    return a * b
"""

code4 = """
for i in range(10):
    print(i)
"""

print("Same Logic:", ast_similarity(code1, code2))       # Expect high
print("Different Operation:", ast_similarity(code1, code3))  # Medium
print("Different Structure:", ast_similarity(code1, code4))  # Low
