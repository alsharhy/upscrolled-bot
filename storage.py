import hashlib
import os

FILE_PATH = "posted_hashes.txt"

def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def is_already_posted(text):
    if not os.path.exists(FILE_PATH):
        return False

    hashed = hash_text(text)
    with open(FILE_PATH, "r") as f:
        return hashed in f.read()

def save_post(text):
    hashed = hash_text(text)
    with open(FILE_PATH, "a") as f:
        f.write(hashed + "\n")