import re

# Python Keywords
PY_KEYWORDS = {
    "def", "return", "if", "else", "for", "while", "class", "import", "from", "as"
}

# Java Keywords
JAVA_KEYWORDS = {
    "class", "public", "private", "protected", "static", "void", "int", "float",
    "double", "return", "if", "else", "for", "while", "new", "import", "package"
}

# C++ Keywords
CPP_KEYWORDS = {
    "int", "float", "double", "return", "if", "else", "for", "while", "class",
    "public", "private", "protected", "void", "include", "using", "namespace"
}

LANG_KEYWORDS = {
    "python": PY_KEYWORDS,
    "java": JAVA_KEYWORDS,
    "cpp": CPP_KEYWORDS
}

def tokenize_code(code: str):    
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|[+\-*/=(){}.;,<>]", code)
    return tokens

def normalize_identifiers(tokens, lang="python"):
    keywords = LANG_KEYWORDS.get(lang, PY_KEYWORDS)
    identifier_map = {}
    normalized_tokens = []
    var_count = 1

    for token in tokens:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token) and token not in keywords:
            if token not in identifier_map:
                identifier_map[token] = f"var{var_count}"
                var_count += 1
            normalized_tokens.append(identifier_map[token])
        else:
            normalized_tokens.append(token)

    return normalized_tokens

if __name__ == "__main__":
    code = "def add(x, y): return x + y"
    tokens = tokenize_code(code)
    norm = normalize_identifiers(tokens)

    print("TOKENS:", tokens)
    print("NORMALIZED:", norm)