from engine.text_similarity import compare_texts

if __name__ == "__main__":
    text1 = input("Enter Text 1: ")
    text2 = input("Enter Text 2: ")

    result = compare_texts(text1, text2)

    print("\n--- Plagiarism Report ---")
    for k, v in result.items():
        print(f"{k}: {v}")
