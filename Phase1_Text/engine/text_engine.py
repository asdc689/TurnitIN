"""
text_engine.py
--------------
Entry point for the text plagiarism engine.
Accepts two file paths, reads them, runs the full analysis, and prints
a detailed report.

Usage:
    python text_engine.py <file_a> <file_b>

Example:
    python text_engine.py essay_original.txt essay_submitted.txt
"""

import sys
import os
import json

# Ensure the text module directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "text"))

from scorer import compute_similarity, format_report


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB hard limit


def validate_file_size(path: str) -> tuple[bool, str]:
    """
    Check whether a file is within the allowed size limit.
    Returns (True, "") if OK, or (False, error_message) if too large.

    Intended for use by the web app layer BEFORE reading the file,
    so it can return a clean 400 error to the user with a friendly message
    rather than reading a huge file into memory first.

    Example web app usage:
        ok, msg = validate_file_size(uploaded_path)
        if not ok:
            return jsonify({"error": msg}), 400
    """
    try:
        size = os.path.getsize(path)
    except OSError as e:
        return False, f"Cannot stat file: {e}"

    if size > MAX_FILE_SIZE_BYTES:
        size_mb = size / (1024 * 1024)
        limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, (
            f"File is {size_mb:.2f} MB which exceeds the {limit_mb} MB limit. "
            f"Please upload a smaller file."
        )
    return True, ""


def read_file(path: str) -> str:
    """
    Read a text file and return its content.
    Rejects files exceeding MAX_FILE_SIZE_BYTES (10 MB) — matching the
    web app's upload limit so CLI and web behave identically.
    """
    try:
        ok, msg = validate_file_size(path)
        if not ok:
            print(f"[Error] {msg}")
            sys.exit(1)

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[Error] File not found: {path}")
        sys.exit(1)
    except Exception as e:
        print(f"[Error] Could not read {path}: {e}")
        sys.exit(1)


def run(file_a: str, file_b: str, output_json: bool = False) -> dict:
    """
    Run the full text plagiarism analysis on two files.

    Args:
        file_a:       Path to first text file
        file_b:       Path to second text file
        output_json:  If True, also saves a JSON report alongside the files

    Returns:
        Full report dict from scorer.compute_similarity
    """
    text_a = read_file(file_a)
    text_b = read_file(file_b)

    name_a = os.path.basename(file_a)
    name_b = os.path.basename(file_b)

    report = compute_similarity(text_a, text_b,
                                 file_a_name=name_a,
                                 file_b_name=name_b)

    print(format_report(report))

    if output_json:
        json_path = "plagiarism_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[Engine] Full JSON report saved to: {json_path}")

    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python text_engine.py <file_a> <file_b> [--json]")
        sys.exit(1)

    fa = sys.argv[1]
    fb = sys.argv[2]
    save_json = "--json" in sys.argv

    run(fa, fb, output_json=save_json)
