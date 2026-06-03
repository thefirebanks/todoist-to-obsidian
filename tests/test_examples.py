import unittest
from pathlib import Path


class ExamplesTest(unittest.TestCase):
    def test_examples_use_placeholders(self):
        root = Path(__file__).resolve().parents[1]
        checked = []
        combined = ""
        for directory in [root / "examples"]:
            for path in directory.rglob("*"):
                if path.is_file():
                    checked.append(path)
                    combined += path.read_text(encoding="utf-8")
        self.assertTrue(checked)
        self.assertIn("/path/to/", combined)


if __name__ == "__main__":
    unittest.main()
