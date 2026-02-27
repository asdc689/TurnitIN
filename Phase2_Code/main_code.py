from engine.code_similarity_engine import compare_code
from utils.language_detector import detect_language


def get_multiline_input(prompt: str) -> str:
    print(prompt)
    print("(Paste code below. Type '<<EOF>>' on a new line and press Enter to finish)")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "<<EOF>>": # Sentinel to stop
                break
            lines.append(line)
        except EOFError:
            break
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

    # Check to see which language is perceived
    # print(f"\n[Detected] Code 1: {lang1.upper()} | Code 2: {lang2.upper()}")

    # ---------- Comparison ----------
    result = compare_code(code1, code2, lang1=lang1, lang2=lang2)

    # ---------- Report ----------
    print("\n--- Code Plagiarism Report ---")
    for k, v in result.items():
        print(f"{k}: {v}")

    print("\n")
