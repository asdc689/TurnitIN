import re

def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)  # keep apostrophes
    text = normalize_whitespace(text)
    return text

