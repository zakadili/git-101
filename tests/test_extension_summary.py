"""Regression tests for the local extension summary utility."""
import importlib.util
import subprocess
import sys
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

    def test_excludes_build_directories_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("", encoding="utf-8")
            for name in module.DEFAULT_EXCLUDED_DIRS:
                (root / name).mkdir()
                (root / name / "generated.js").write_text("", encoding="utf-8")
            self.assertEqual(module.count_extensions(root), {".py": 1})
            self.assertEqual(
                module.count_extensions(root, excluded_dirs=()),
                {".py": 1, ".js": len(module.DEFAULT_EXCLUDED_DIRS)},
            )

    def test_cli_can_include_build_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("", encoding="utf-8")
            (root / "app.py").write_text("", encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(root)]
            normal = subprocess.run(command, capture_output=True, text=True, check=True)
            included = subprocess.run(command + ["--include-build-dirs"], capture_output=True, text=True, check=True)
            self.assertIn(".py", normal.stdout)
            self.assertNotIn("[no extension]", normal.stdout)
            self.assertIn("[no extension]", included.stdout)


if __name__ == "__main__":
    unittest.main()
