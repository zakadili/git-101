#!/usr/bin/env python3
"""Summarize file extensions in a local directory without following symlinks."""
from collections import Counter
from pathlib import Path
import argparse

def count_extensions(root: Path) -> Counter:
    counts = Counter()
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            counts[path.suffix.lower() or "[no extension]"] += 1
    return counts

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.directory).expanduser()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")
    for ext, count in count_extensions(root).most_common():
        print(f"{ext:20} {count}")

if __name__ == "__main__":
    main()
