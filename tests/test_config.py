import os
import stat
import tempfile
import unittest
from pathlib import Path

from todoist_obsidian_bridge.config import (
    AppConfig,
    ConfigError,
    ObsidianConfig,
    TodoistConfig,
    load_dotenv,
    load_config,
    render_config,
    write_config,
)


class ConfigTest(unittest.TestCase):
    def test_round_trips_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.toml"
            state_path = root / "state.json"
            config = AppConfig(
                todoist=TodoistConfig(project="obs", label="capture"),
                obsidian=ObsidianConfig(vault_path=root / "Vault", default_note="Inbox.md"),
                aliases={"project": "Projects/project notes.md"},
                state_path=state_path,
                config_path=config_path,
            )
            write_config(config)
            loaded = load_config(config_path)
            self.assertEqual(loaded.todoist.project, "obs")
            self.assertEqual(loaded.todoist.label, "capture")
            self.assertEqual(loaded.aliases["project"], "Projects/project notes.md")

    def test_rendered_config_has_no_secret_token_field(self):
        config = AppConfig(
            todoist=TodoistConfig(),
            obsidian=ObsidianConfig(vault_path=Path("/path/to/vault"), default_note="Inbox.md"),
        )
        rendered = render_config(config)
        self.assertNotIn("TODOIST_API_TOKEN", rendered)
        self.assertNotIn("token", rendered.lower())

    @unittest.skipIf(os.name != "posix", "POSIX permission check")
    def test_refuses_world_readable_dotenv(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("TODOIST_API_TOKEN=test\n", encoding="utf-8")
            env_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            with self.assertRaises(ConfigError):
                load_dotenv(env_path)


if __name__ == "__main__":
    unittest.main()
