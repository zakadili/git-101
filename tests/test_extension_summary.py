"""Regression tests for the local extension summary utility."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "extension_summary.py"
spec = importlib.util.spec_from_file_location("extension_summary", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExtensionSummaryTests(unittest.TestCase):
    def test_counts_nested_files_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            (root / "one.PY").write_text("", encoding="utf-8")
            (root / "nested" / "two.py").write_text("", encoding="utf-8")
            (root / "README").write_text("", encoding="utf-8")
            self.assertEqual(module.count_extensions(root), {".py": 2, "[no extension]": 1})

    def test_ignores_file_and_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real.txt").write_text("", encoding="utf-8")
            (root / "linked.txt").symlink_to(root / "real.txt")
            outside = root / "outside"
            outside.mkdir()
            (outside / "source.md").write_text("", encoding="utf-8")
            (root / "linked-dir").symlink_to(outside, target_is_directory=True)
            self.assertEqual(module.count_extensions(root), {".txt": 1, ".md": 1})


if __name__ == "__main__":
    unittest.main()
