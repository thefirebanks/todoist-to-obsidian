import datetime as dt
import unittest

from todoist_obsidian_bridge.config import FormatConfig
from todoist_obsidian_bridge.formatting import heading_time, markdown_block


class FormattingTest(unittest.TestCase):
    def test_human_long_heading_uses_created_at(self):
        task = {"created_at": "2026-01-21T19:16:00Z"}
        formatted = heading_time(task, FormatConfig(), timezone=dt.timezone.utc)
        self.assertEqual(formatted, "Wednesday, January 21, 2026 7:16 PM")

    def test_markdown_omits_alias_and_includes_description(self):
        task = {
            "created_at": "2026-01-21T19:16:00Z",
            "description": "More detail",
            "url": "",
            "labels": [],
        }
        block = markdown_block(task, [], "Capture text", FormatConfig())
        self.assertIn("## Wednesday", block)
        self.assertIn("Capture text", block)
        self.assertIn("More detail", block)
        self.assertNotIn("Alias:", block)


if __name__ == "__main__":
    unittest.main()
