# from engine.code_similarity_engine import compare_code
# from utils.language_detector import detect_language

# if __name__ == "__main__":

#     print("Enter Code 1 (end with an empty line):")
#     lines = []
#     while True:
#         line = input()
#         if line.strip() == "":
#             break
#         lines.append(line)
#     code1 = "\n".join(lines)

#     print("\nEnter Code 2 (end with an empty line):")
#     lines = []
#     while True:
#         line = input()
#         if line.strip() == "":
#             break
#         lines.append(line)
#     code2 = "\n".join(lines)

#     lang1 = detect_language(code1)
#     lang2 = detect_language(code2)

#     result = compare_code(code1, code2, lang1, lang2)

#     print("\n--- Code Plagiarism Report ---")
#     for k, v in result.items():
#         print(f"{k}: {v}")

#     print("\n")



from engine.code_similarity_engine import compare_code
from utils.language_detector import detect_language


def get_multiline_input(prompt: str) -> str:
    print(prompt)
    print("(Paste code below. Press ENTER on an empty line to finish)")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":

    # ---------- Input ----------
    code1 = get_multiline_input("\n--- ENTER CODE 1 ---")
    if not code1.strip():
        print("Error: Code 1 is empty.")
        exit(1)

    code2 = get_multiline_input("\n--- ENTER CODE 2 ---")
    if not code2.strip():
        print("Error: Code 2 is empty.")
        exit(1)

    # ---------- Language Detection ----------
    lang1 = detect_language(code1)
    lang2 = detect_language(code2)

    # ---------- Comparison ----------
    result = compare_code(code1, code2, lang1=lang1, lang2=lang2)

    # ---------- Report ----------
    print("\n--- Code Plagiarism Report ---")
    for k, v in result.items():
        print(f"{k}: {v}")

    print("\n")
