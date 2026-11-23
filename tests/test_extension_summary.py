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


    def test_cli_reports_missing_directory_as_usage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(missing)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Not a directory:", result.stderr)

    def test_cli_orders_by_count_then_extension_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("one.TXT", "two.txt", "one.py", "two.PY", "single.md"):
                (root / filename).write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root)],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(
                [line.split()[0] for line in result.stdout.splitlines()],
                [".py", ".txt", ".md"],
            )


    def test_cli_json_and_custom_exclusion(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skip").mkdir()
            (root / "skip" / "ignored.py").write_text("", encoding="utf-8")
            (root / "keep.PY").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--json", "--exclude-dir", "skip"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {".py": 1})

    def test_cli_rejects_exclusion_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory, "--exclude-dir", "foo/bar"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("expects a directory name", result.stderr)


    def test_cli_custom_exclusion_applies_at_every_depth(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skip").mkdir()
            (root / "skip" / "first.py").write_text("", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "skip").mkdir()
            (root / "nested" / "skip" / "second.py").write_text("", encoding="utf-8")
            (root / "nested" / "keep.py").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--exclude-dir", "skip", "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {".py": 1})

    def test_cli_custom_exclusion_still_applies_when_build_dirs_included(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("", encoding="utf-8")
            (root / "skip").mkdir()
            (root / "skip" / "ignored.py").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--include-build-dirs",
                 "--exclude-dir", "skip", "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {"[no extension]": 1})


    def test_cli_empty_directory_outputs_empty_json(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory, "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {})

    def test_cli_multiple_excluded_directory_names(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("cache", "generated", "src"):
                (root / name).mkdir()
                (root / name / "file.py").write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--json",
                 "--exclude-dir", "cache", "--exclude-dir", "generated"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {".py": 1})


    def test_cli_min_count_filters_rare_extensions(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ("one.py", "two.PY", "single.md"):
                (root / filename).write_text("", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--min-count", "2", "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {".py": 2})

    def test_cli_min_count_rejects_nonpositive_values(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory, "--min-count", "0"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--min-count must be a positive integer", result.stderr)

if __name__ == "__main__":
    unittest.main()
