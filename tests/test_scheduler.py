import unittest
from pathlib import Path

from todoist_obsidian_bridge.scheduler.core import ScheduleError, parse_schedule
from todoist_obsidian_bridge.scheduler.launchd import render_plist
from todoist_obsidian_bridge.scheduler.systemd import render_timer
from todoist_obsidian_bridge.scheduler.windows_task import render_task_xml


class SchedulerTest(unittest.TestCase):
    def test_interval_parsing(self):
        schedule = parse_schedule(every="1h")
        self.assertEqual(schedule.seconds, 3600)

    def test_daily_validation(self):
        schedule = parse_schedule(daily_at="21:30")
        self.assertEqual(schedule.kind, "daily")
        with self.assertRaises(ScheduleError):
            parse_schedule(daily_at="25:99")

    def test_templates_render_without_personal_paths(self):
        command = ["/path/to/python", "-m", "todoist_obsidian_bridge"]
        config = Path("/path/to/config.toml")
        schedule = parse_schedule(every="1h")
        rendered = "\n".join(
            [
                render_plist(command, config, schedule, Path("/path/to/logs")),
                render_timer(schedule),
                render_task_xml(command, config, schedule),
            ]
        )
        self.assertIn("3600", rendered)
        self.assertIn("/path/to/config.toml", rendered)


if __name__ == "__main__":
    unittest.main()
