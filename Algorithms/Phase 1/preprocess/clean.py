import re

def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)  # keep apostrophes
    text = normalize_whitespace(text)
    return text


if __name__ == "__main__":
    sample = "This is a Sample, text!!! With EXTRA   spaces."
    print("RAW:", sample)
    print("CLEANED:", clean_text(sample))
