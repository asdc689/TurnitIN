from Phase3_Unified.engine.unified_analyzer import analyze_submission

# -------- TEXT TEST --------
print("----- TEXT TEST -----")
res_text = analyze_submission(
    "Plagiarism detection system",
    "Plagiarism detection system",
    mode="text"
)
print(res_text)

# -------- CODE TEST --------
print("\n----- CODE TEST -----")
code1 = "def add(a,b): return a+b"
code2 = "def add(x,y): return x+y"

res_code = analyze_submission(
    code1,
    code2,
    mode="code"
)
print(res_code)
