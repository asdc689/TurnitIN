import re

def normalize_whitespace(code: str) -> str:
    """
    Shared function to normalize whitespace:
    Replaces tabs, newlines, and multiple spaces with a single space.
    """
    return re.sub(r"\s+", " ", code).strip()


def clean_python(code: str) -> str:
    """
    Cleaning rules specific to Python:
    - Removes # single-line comments
    - Removes \"\"\" and ''' multi-line docstrings
    """
    # Remove multi-line comments (Docstrings)
    code = re.sub(r'"""[\s\S]*?"""', "", code)
    code = re.sub(r"'''[\s\S]*?'''", "", code)    
    # Remove single-line comments (Hash)
    code = re.sub(r"#.*?$", "", code, flags=re.MULTILINE)    
    return normalize_whitespace(code)


def clean_java(code: str) -> str:
    """
    Cleaning rules specific to Java:
    - Removes // single-line comments
    - Removes /* */ multi-line comments
    """
    # Remove multi-line comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)    
    # Remove single-line comments (Double slash)
    code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)    
    return normalize_whitespace(code)


def clean_cpp(code: str) -> str:
    """
    Cleaning rules specific to C++:
    - Removes // single-line comments
    - Removes /* */ multi-line comments
    - CRITICAL: Does NOT remove '#' so headers like #include <iostream> stay intact.
    """
    # Remove multi-line comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)    
    # Remove single-line comments (Double slash)
    code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)    
    return normalize_whitespace(code)


def clean_code(code: str, lang: str) -> str:
    """
    Dispatcher function. 
    'lang' is REQUIRED. No default value.
    """
    if not lang:
        raise ValueError("Language must be specified for cleaning.")
        
    lang = lang.lower()

    if lang == "java":
        return clean_java(code)
    elif lang == "cpp":
        return clean_cpp(code)
    elif lang in ["python", "py"]:
        return clean_python(code)
    else:
        # Safety fallback: If we don't know the language, 
        # assume Python (or return raw code if you prefer).
        return clean_python(code)
