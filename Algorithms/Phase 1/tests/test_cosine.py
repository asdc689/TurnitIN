from algorithms.cosine import cosine_sim

# Similar text
t1 = "plagiarism detection system compares documents"
t2 = "document similarity system detects plagiarism"
print("Test 1:", cosine_sim(t1, t2))  # Expect > 0.5

# Different text
t3 = "football is a popular sport"
t4 = "machine learning models detect fraud"
print("Test 2:", cosine_sim(t3, t4))  # Expect < 0.3
