from engine.code_similarity import compare_code

code1 = """
def add(a, b):
    return a + b
"""

code2 = """
def sum(x, y):
    res = x + y
    return res
"""

code3 = """
for i in range(10):
    print(i)
"""

print("Similar Code:", compare_code(code1, code2))
print("Different Code:", compare_code(code1, code3))
