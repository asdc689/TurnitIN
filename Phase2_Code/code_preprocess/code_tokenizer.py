import re

# -------------------------------------------------------------------------
# 1. COMPREHENSIVE KEYWORD LISTS
# -------------------------------------------------------------------------

# Python 3 Keywords
PY_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is", "lambda",
    "nonlocal", "not", "or", "pass", "raise", "return", "try", "while",
    "with", "yield", "print", "range", "self", "len", "str", "int", "float",
    "list", "dict", "set", "tuple", "super", "__init__"
}

# Java Keywords (Standard + Contextual)
JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
    "var", "String", "System", "out", "println", "main", "Override"
}

# C++ Keywords (C++17/20 Standards)
CPP_KEYWORDS = {
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor",
    "bool", "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t",
    "class", "compl", "concept", "const", "const_cast", "consteval", "constexpr",
    "constinit", "continue", "co_await", "co_return", "co_yield", "decltype",
    "default", "delete", "do", "double", "dynamic_cast", "else", "enum",
    "explicit", "export", "extern", "false", "float", "for", "friend", "goto",
    "if", "inline", "int", "long", "mutable", "namespace", "new", "noexcept",
    "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
    "protected", "public", "register", "reinterpret_cast", "requires", "return",
    "short", "signed", "sizeof", "static", "static_assert", "static_cast",
    "struct", "switch", "template", "this", "thread_local", "throw", "true",
    "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
    "include", "define", "ifdef", "endif", "std", "cout", "cin", "endl", "vector", "string"
}

# Map for easy lookup
LANG_KEYWORDS = {
    "python": PY_KEYWORDS,
    "java": JAVA_KEYWORDS,
    "cpp": CPP_KEYWORDS
}


# -------------------------------------------------------------------------
# 2. LANGUAGE-SPECIFIC TOKENIZERS
# -------------------------------------------------------------------------

def tokenize_python(code: str) -> list:
    """
    Python Tokenizer:
    - Standard operators
    - Ignores specific C++ operators like '::' or '->'
    """
    # Regex captures: Identifiers, Numbers, Comparison Ops, Brackets, Math/Logic Ops
    # Added: [ ] % ! & | ^
    pattern = r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|[+\-*/=(){}.;,<>[\]%!&|^]"
    return re.findall(pattern, code)


def tokenize_java(code: str) -> list:
    """
    Java Tokenizer:
    - Similar to Python but handles annotations (@Interface) if needed in future
    """
    # Standard Java operators + Annotations (@)
    pattern = r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|&&|\|\||[+\-*/=(){}.;,<>[\]%!&|^@]"
    return re.findall(pattern, code)


def tokenize_cpp(code: str) -> list:
    """
    C++ Tokenizer:
    - Captures scope resolution '::'
    - Captures pointer access '->'
    - Captures preprocessor directives '#'
    """
    # We explicitly add '::' and '->' to the regex so they are treated as single tokens
    # rather than split into ':', ':', '-', '>'
    pattern = r"::|->|[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|&&|\|\||[+\-*/=(){}.;,<>[\]%!&|^#]"
    return re.findall(pattern, code)


def tokenize_code(code: str, lang: str) -> list:    
    """
    Dispatcher: Tokenizes based on the specific language rules.
    """
    if not lang:
        raise ValueError("Language must be specified for tokenization.")
        
    lang = lang.lower()

    if lang == "java":
        return tokenize_java(code)
    elif lang == "cpp":
        return tokenize_cpp(code)
    elif lang in ["python", "py"]:
        return tokenize_python(code)
    else:
        # Fallback to Python-style if unknown
        return tokenize_python(code)


# -------------------------------------------------------------------------
# 3. IDENTIFIER NORMALIZATION
# -------------------------------------------------------------------------

def normalize_identifiers(tokens: list, lang: str) -> list:
    """
    Replaces non-keyword identifiers with generic placeholders (var1, var2...)
    to detect logic similarity despite variable renaming.
    """
    if not lang:
        raise ValueError("Language must be specified for normalization.")
        
    lang = lang.lower()
    # STRICT CHECK: If language is not supported, we should not guess keywords.
    if lang not in LANG_KEYWORDS:
        # Fallback to Python keywords is DANGEROUS for C++/Java.
        # But if the lang is 'unknown', we might just skip normalization 
        # to avoid destroying the code.
        # However, since we auto-detected 'cpp'/'java'/'python', we are safe.
        # If 'unknown', we default to Python keywords as a best-effort.
        keywords = PY_KEYWORDS
    else:
        keywords = LANG_KEYWORDS[lang]

    identifier_map = {}
    normalized_tokens = []
    var_count = 1

    for token in tokens:
        # Check if token is a valid identifier (word) AND not a keyword
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            if token not in keywords:
                # It is a variable/function name -> Normalize it
                if token not in identifier_map:
                    identifier_map[token] = f"var{var_count}"
                    var_count += 1
                normalized_tokens.append(identifier_map[token])
            else:
                # It is a keyword (like 'int' or 'vector') -> Keep as is
                normalized_tokens.append(token)
        else:
            # It is an operator/symbol -> Keep as is
            normalized_tokens.append(token)

    return normalized_tokens