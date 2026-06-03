from __future__ import annotations

import os
import platform
from pathlib import Path


APP_NAME = "todoist-to-obsidian"


def app_config_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if system == "Windows":
        root = os.environ.get("APPDATA")
        return Path(root) / APP_NAME if root else Path.home() / "AppData" / "Roaming" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def app_state_dir() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    if system == "Windows":
        root = os.environ.get("LOCALAPPDATA")
        return Path(root) / APP_NAME if root else Path.home() / "AppData" / "Local" / APP_NAME
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / APP_NAME


def default_config_path() -> Path:
    return app_config_dir() / "config.toml"


def default_env_path() -> Path:
    return app_config_dir() / ".env"


def default_state_path() -> Path:
    return app_state_dir() / "state.json"
