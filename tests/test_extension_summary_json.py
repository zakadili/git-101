"""Machine-readable output regression tests for extension_summary."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "extension_summary.py"


class JsonOutputTests(unittest.TestCase):
    def test_json_output_respects_exclusions_and_case(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one.TXT").write_text("", encoding="utf-8")
            (root / "two.txt").write_text("", encoding="utf-8")
            (root / "README").write_text("", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "ignored.py").write_text("", encoding="utf-8")
            command = [sys.executable, str(SCRIPT), str(root), "--json"]
            normal = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(normal.stdout), {".txt": 2, "[no extension]": 1})
            included = subprocess.run(command + ["--include-build-dirs"], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(included.stdout), {".py": 1, ".txt": 2, "[no extension]": 1})

    def test_json_output_for_empty_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), directory, "--json"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), {})


if __name__ == "__main__":
    unittest.main()
