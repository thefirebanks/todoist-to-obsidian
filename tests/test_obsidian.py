import tempfile
import unittest
from pathlib import Path

from todoist_obsidian_bridge.obsidian import ObsidianError, append_blocks, resolve_note_path


class ObsidianTest(unittest.TestCase):
    def test_appends_to_default_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            written, warnings = append_blocks(vault, "Inbox.md", {"Inbox.md": ["hello"]})
            self.assertEqual(warnings, [])
            self.assertEqual(written, [(vault / "Inbox.md").resolve()])
            self.assertEqual((vault / "Inbox.md").read_text(encoding="utf-8"), "hello\n")

    def test_missing_alias_target_falls_back_to_default_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            written, warnings = append_blocks(vault, "Inbox.md", {"Missing.md": ["hello"]})
            self.assertTrue(warnings)
            self.assertEqual(written, [(vault / "Inbox.md").resolve()])
            self.assertEqual((vault / "Inbox.md").read_text(encoding="utf-8"), "hello\n")

    def test_note_path_cannot_escape_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            with self.assertRaises(ObsidianError):
                resolve_note_path(vault, "../outside.md")
            with self.assertRaises(ObsidianError):
                resolve_note_path(vault, "/tmp/outside.md")


if __name__ == "__main__":
    unittest.main()
