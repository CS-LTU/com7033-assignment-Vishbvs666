import os

HEADER = """'''
===========================================================
StrokeCare Web Application — Secure Software Development
Author: Vishvapriya Sangvikar

Course: COM7033 – MSc Data Science & Artificial Intelligence
Student ID: 2415083
Institution: Leeds Trinity University
Assessment: Assessment 1 – Software Artefact (70%)
AI Statement: Portions of this file were drafted or refined using
    generative AI for planning and editing only,
    as permitted in the module brief.
===========================================================
'''
"""

# folders to skip
SKIP_DIRS = {"venv", ".venv", "__pycache__", "node_modules", ".git"}

def should_skip(path):
    for skip in SKIP_DIRS:
        if skip in path.split(os.sep):
            return True
    return False

def add_header_to_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # If header already exists, skip
    if "StrokeCare Web Application" in content:
        print(f"HEADER EXISTS → Skipped: {filepath}")
        return

    # Avoid breaking shebangs (#!)
    if content.startswith("#!"):
        lines = content.split("\n")
        shebang = lines[0]
        file_body = "\n".join(lines[1:])
        new_content = shebang + "\n" + HEADER + "\n" + file_body
    else:
        new_content = HEADER + "\n" + content

    with open(filepath, "w") as f:
        f.write(new_content)

    print(f"HEADER ADDED → {filepath}")

def scan_and_update(root):
    for folder, subdirs, files in os.walk(root):
        if should_skip(folder):
            continue
        for file in files:
            if file.endswith(".py"):
                add_header_to_file(os.path.join(folder, file))

if __name__ == "__main__":
    scan_and_update(".")
