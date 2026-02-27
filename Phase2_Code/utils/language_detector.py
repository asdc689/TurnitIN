def detect_language(code: str) -> str:
    """
    Heuristic-based language detection for Python, C++, Java.
    All signal matching is case-insensitive EXCEPT Java-specific
    signals that rely on capitalisation (e.g. 'String' vs 'string',
    'System.out', '@Override') — those are checked against the
    original code to avoid false positives.
    Returns: 'python', 'cpp', or 'java'
    """
    code_lower = code.lower()

    # ---- Python indicators (case-insensitive) ----
    python_signals = [
        "def ", "import ", "self", "elif ", "pass",
        "print(", "range(", "__init__", "str(", "len(", "yield "
    ]

    # ---- C++ indicators (case-insensitive) ----
    cpp_signals = [
        "#include", "std::", "using namespace", "->", "::",
        "cout", "cin", "nullptr", "template",
        "auto ", "vector<", "struct ", "virtual",
        "int main", "void main"
    ]

    # ---- Java indicators ----
    # Checked against original code (case-sensitive) because Java relies
    # on capitalisation to distinguish types e.g. String vs string,
    # Integer vs integer, System vs system.
    java_signals = [
        "public class", "public int", "static void main", "System.out",
        "Math.", ".charAt", "implements", "extends", "package ", "throws ",
        "String ", "boolean ", "ArrayList", "HashMap", "List<",
        "@Override", "Integer", "interface "
    ]

    # Python and C++ scored on lowercased code for robustness
    python_score = sum(1 for s in python_signals if s in code_lower)
    cpp_score    = sum(1 for s in cpp_signals    if s in code_lower)
    # Java scored on original code to preserve case-sensitive signals
    java_score   = sum(1 for s in java_signals   if s in code)

    scores = {
        "python": python_score,
        "cpp":    cpp_score,
        "java":   java_score
    }

    # Pick the language with the highest signal count
    detected = max(scores, key=scores.get)

    # Fallback: if no signals matched at all, default to python
    if scores[detected] == 0:
        return "python"

    return detected