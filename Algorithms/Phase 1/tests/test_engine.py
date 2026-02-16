from engine.text_similarity import compare_texts

t1 = "Plagiarism detection system compares documents."
t2 = "Document similarity system detects plagiarism."

t3 = "Football is a popular sport."
t4 = "Machine learning models detect fraud."

print("SIMILAR TEXT RESULT:")
print(compare_texts(t1, t2))

print("\nDIFFERENT TEXT RESULT:")
print(compare_texts(t3, t4))
