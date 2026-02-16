from algorithms.jaccard import jaccard_similarity

# Case 1: identical
A = ["a", "b", "c"]
B = ["a", "b", "c"]
print("Test 1:", jaccard_similarity(A, B))  # Expect 1.0

# Case 2: partial overlap
A = ["a", "b", "c"]
B = ["a", "d", "e"]
print("Test 2:", jaccard_similarity(A, B))  # Expect 0.2

# Case 3: no overlap
A = ["x", "y"]
B = ["a", "b"]
print("Test 3:", jaccard_similarity(A, B))  # Expect 0.0

# Case 4: empty
A = []
B = []
print("Test 4:", jaccard_similarity(A, B))  # Expect 1.0
