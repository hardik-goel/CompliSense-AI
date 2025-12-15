import hashlib
from pathlib import Path

def hash_directory(root: Path):
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()
