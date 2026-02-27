from algorithms.lcs import lcs_similarity

# Case 1: identical
A = ["a", "b", "c"]
B = ["a", "b", "c"]
print("Test 1:", lcs_similarity(A, B))  # Expect 1.0

# Case 2: partial
A = ["this", "is", "a", "test"]
B = ["this", "is", "test"]
print("Test 2:", lcs_similarity(A, B))  # Expect 1.0

# Case 3: different
A = ["a", "b"]
B = ["x", "y"]
print("Test 3:", lcs_similarity(A, B))  # Expect 0.0

# Case 4: reordered words
A = ["plagiarism", "detection", "system"]
B = ["system", "plagiarism", "detection"]
print("Test 4:", lcs_similarity(A, B))  # Expect < 1.0
