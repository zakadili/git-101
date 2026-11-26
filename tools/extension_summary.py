#!/usr/bin/env python3
"""Summarize local file extensions, excluding symlinks and build directories."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

DEFAULT_EXCLUDED_DIRS = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__"})


def _raise_walk_error(error: OSError) -> None:
    """Do not silently return incomplete counts when a directory cannot be read."""
    raise error


def count_extensions(root: Path, excluded_dirs=DEFAULT_EXCLUDED_DIRS) -> Counter:
    """Count files by lowercase suffix, without traversing symlinked directories."""
    counts = Counter()
    for directory, subdirs, filenames in os.walk(root, followlinks=False, onerror=_raise_walk_error):
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
    parser.add_argument(
        "--exclude-dir", action="append", default=[], metavar="NAME",
        help="Exclude a directory name at any depth (repeatable)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output extension counts as a JSON object for scripts",
    )
    parser.add_argument(
        "--min-count", type=int, default=1, metavar="N",
        help="Show only extensions with at least N files (default: 1)",
    )
    args = parser.parse_args()
    if args.min_count < 1:
        parser.error("--min-count must be a positive integer")
    root = Path(args.directory).expanduser()
    if root.is_symlink():
        parser.error(f"Directory must not be a symlink: {root}")
    if not root.is_dir():
        parser.error(f"Not a directory: {root}")
    for name in args.exclude_dir:
        if name in (".", "..") or name != Path(name).name or not name:
            parser.error(f"--exclude-dir expects a directory name, not a path: {name!r}")
    excluded = set() if args.include_build_dirs else set(DEFAULT_EXCLUDED_DIRS)
    excluded.update(args.exclude_dir)
    try:
        counts = count_extensions(root, excluded_dirs=excluded)
    except OSError as error:
        parser.error(f"Cannot scan directory: {error}")
    counts = {ext: count for ext, count in counts.items() if count >= args.min_count}
    if args.json:
        print(json.dumps(dict(sorted(counts.items())), indent=2))
    else:
        for ext, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            print(f"{ext:20} {count}")


if __name__ == "__main__":
    main()
