import re

def remove_comments(code: str) -> str:
    # Remove single-line comments
    code = re.sub(r"//.*?$", "", code, flags=re.MULTILINE)
    code = re.sub(r"#.*?$", "", code, flags=re.MULTILINE)

    # Remove multi-line comments
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    code = re.sub(r'"""[\s\S]*?"""', "", code)
    code = re.sub(r"'''[\s\S]*?'''", "", code)

    return code

def normalize_whitespace(code: str) -> str:
    return re.sub(r"\s+", " ", code).strip()

def clean_code(code: str) -> str:
    code = remove_comments(code)
    code = normalize_whitespace(code)
    return code

if __name__ == "__main__":
    sample = """
    # This is a comment
    def add(a, b):
        return a + b  # inline comment
    """
    print("CLEANED CODE:\n", clean_code(sample))
