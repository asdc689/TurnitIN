def detect_language(code: str) -> str:
    """
    Heuristic-based language detection for Python, C++, Java.
    Returns: 'python', 'cpp', or 'java'
    """

    code_lower = code.lower()

    # ---- Python indicators ----
    python_signals = [
        "def ", "import ", "self", "elif ", "None", "True", "False",
        ":", "print(", "range("
    ]

    # ---- C++ indicators ----
    cpp_signals = [
        "#include", "std::", "using namespace", "->", "::",
        "cout", "cin", "<bits/stdc++.h>", "template<", "vector"
    ]

    # ---- Java indicators ----
    java_signals = [
        "public class", "static void main", "System.out",
        "new ", "implements", "extends", "package "
    ]

    python_score = sum(1 for s in python_signals if s in code)
    cpp_score = sum(1 for s in cpp_signals if s in code)
    java_score = sum(1 for s in java_signals if s in code)

    scores = {
        "python": python_score,
        "cpp": cpp_score,
        "java": java_score
    }

    # Pick the language with the highest signal
    detected = max(scores, key=scores.get)

    # Fallback safety
    if scores[detected] == 0:
        return "python"  # safe default

    return detected
