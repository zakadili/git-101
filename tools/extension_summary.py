#!/usr/bin/env python3
"""Summarize local file extensions, excluding symlinks and build directories."""
import argparse
import os
from collections import Counter
from pathlib import Path

DEFAULT_EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__"})


def count_extensions(root: Path, excluded_dirs=DEFAULT_EXCLUDED_DIRS) -> Counter:
    """Count files by lowercase suffix, without traversing symlinked directories."""
    counts = Counter()
    for directory, subdirs, filenames in os.walk(root, followlinks=False):
        subdirs[:] = [
            name for name in subdirs
            if name not in excluded_dirs and not (Path(directory) / name).is_symlink()
        ]
        for filename in filenames:
            path = Path(directory) / filename
            if path.is_symlink() or not path.is_file():
                continue
            counts[path.suffix.lower() or "[no extension]"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument(
        "--include-build-dirs", action="store_true",
        help="Include .git, virtual environments, node_modules and __pycache__",
    )
    args = parser.parse_args()
    root = Path(args.directory).expanduser()
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")
    excluded = () if args.include_build_dirs else DEFAULT_EXCLUDED_DIRS
    counts = count_extensions(root, excluded_dirs=excluded)
    for ext, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"{ext:20} {count}")


if __name__ == "__main__":
    main()
