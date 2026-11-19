"""Tests for repeatable custom directory exclusions."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "extension_summary.py"


class CustomExclusionTests(unittest.TestCase):
    def test_excludes_named_directories_at_multiple_depths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("src", "src/cache", "cache", "src/vendor"):
                (root / name).mkdir(parents=True, exist_ok=True)
            for filename in ("src/main.py", "src/cache/old.py", "cache/old.py", "src/vendor/third.py"):
                (root / filename).write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--json", "--exclude-dir", "cache", "--exclude-dir", "vendor"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {".py": 1})

    def test_custom_exclusions_still_apply_when_build_dirs_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (".git", "cache"):
                (root / name).mkdir()
            (root / ".git" / "config").write_text("", encoding="utf-8")
            (root / "cache" / "old.py").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--json", "--include-build-dirs", "--exclude-dir", "cache"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {"[no extension]": 1})

    def test_rejects_paths_as_directory_names(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory, "--exclude-dir", "src/cache"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("expects a directory name", result.stderr)


if __name__ == "__main__":
    unittest.main()
