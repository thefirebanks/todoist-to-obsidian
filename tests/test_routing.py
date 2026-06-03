import unittest

from todoist_obsidian_bridge.routing import resolve_target_and_content


class RoutingTest(unittest.TestCase):
    def test_alias_routes_and_strips_prefix(self):
        target, content, alias = resolve_target_and_content(
            "project: ship the thing",
            {"project": "Projects/project notes.md"},
            "Inbox.md",
        )
        self.assertEqual(target, "Projects/project notes.md")
        self.assertEqual(content, "ship the thing")
        self.assertEqual(alias, "project")

    def test_unknown_prefix_uses_default(self):
        target, content, alias = resolve_target_and_content("plain capture", {}, "Inbox.md")
        self.assertEqual(target, "Inbox.md")
        self.assertEqual(content, "plain capture")
        self.assertIsNone(alias)


if __name__ == "__main__":
    unittest.main()
