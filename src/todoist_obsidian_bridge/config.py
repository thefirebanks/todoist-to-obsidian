from __future__ import annotations

import os
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .paths import default_config_path, default_env_path, default_state_path


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class TodoistConfig:
    project: str = "obs"
    label: str = ""
    filter_query: str = ""
    close_after_import: bool = True


@dataclass(frozen=True)
class ObsidianConfig:
    vault_path: Path = Path()
    default_note: str = "Inbox.md"


@dataclass(frozen=True)
class FormatConfig:
    heading_format: str = "human_long"
    heading_time_source: str = "todoist_created_at"
    include_source: bool = True
    include_labels: bool = True


@dataclass(frozen=True)
class AppConfig:
    todoist: TodoistConfig
    obsidian: ObsidianConfig
    fmt: FormatConfig = field(default_factory=FormatConfig)
    aliases: dict[str, str] = field(default_factory=dict)
    state_path: Path = field(default_factory=default_state_path)
    config_path: Path = field(default_factory=default_config_path)


def _as_bool(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def load_config(path: Path | None = None) -> AppConfig:
    config_path = (path or default_config_path()).expanduser()
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}. Run `todoist-to-obsidian init`.")

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    todoist_data = data.get("todoist", {})
    obsidian_data = data.get("obsidian", {})
    format_data = data.get("format", {})
    aliases = data.get("aliases", {})
    state_data = data.get("state", {})

    vault_path = str(obsidian_data.get("vault_path", "")).strip()
    if not vault_path:
        raise ConfigError("Missing [obsidian] vault_path in config.")

    if not isinstance(aliases, dict):
        raise ConfigError("[aliases] must be a table of alias = relative_note_path entries.")

    clean_aliases = {str(k).strip(): str(v).strip() for k, v in aliases.items() if str(k).strip() and str(v).strip()}

    return AppConfig(
        todoist=TodoistConfig(
            project=str(todoist_data.get("project", "obs")).strip(),
            label=str(todoist_data.get("label", "")).strip(),
            filter_query=str(todoist_data.get("filter_query", "")).strip(),
            close_after_import=_as_bool(todoist_data.get("close_after_import"), True),
        ),
        obsidian=ObsidianConfig(
            vault_path=Path(vault_path).expanduser(),
            default_note=str(obsidian_data.get("default_note", "Inbox.md")).strip() or "Inbox.md",
        ),
        fmt=FormatConfig(
            heading_format=str(format_data.get("heading_format", "human_long")).strip() or "human_long",
            heading_time_source=str(format_data.get("heading_time_source", "todoist_created_at")).strip()
            or "todoist_created_at",
            include_source=_as_bool(format_data.get("include_source"), True),
            include_labels=_as_bool(format_data.get("include_labels"), True),
        ),
        aliases=clean_aliases,
        state_path=Path(str(state_data.get("path", default_state_path()))).expanduser(),
        config_path=config_path,
    )


def _toml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_config(config: AppConfig) -> str:
    lines = [
        "[todoist]",
        f"project = {_toml_string(config.todoist.project)}",
        f"label = {_toml_string(config.todoist.label)}",
        f"filter_query = {_toml_string(config.todoist.filter_query)}",
        f"close_after_import = {str(config.todoist.close_after_import).lower()}",
        "",
        "[obsidian]",
        f"vault_path = {_toml_string(str(config.obsidian.vault_path))}",
        f"default_note = {_toml_string(config.obsidian.default_note)}",
        "",
        "[format]",
        f"heading_time_source = {_toml_string(config.fmt.heading_time_source)}",
        f"heading_format = {_toml_string(config.fmt.heading_format)}",
        f"include_source = {str(config.fmt.include_source).lower()}",
        f"include_labels = {str(config.fmt.include_labels).lower()}",
        "",
        "[state]",
        f"path = {_toml_string(str(config.state_path))}",
        "",
        "[aliases]",
    ]
    for alias, target in sorted(config.aliases.items()):
        lines.append(f"{alias} = {_toml_string(target)}")
    lines.append("")
    return "\n".join(lines)


def write_config(config: AppConfig, overwrite: bool = False) -> None:
    if config.config_path.exists() and not overwrite:
        raise ConfigError(f"Config already exists: {config.config_path}")
    config.config_path.parent.mkdir(parents=True, exist_ok=True)
    config.config_path.write_text(render_config(config), encoding="utf-8")


def write_env_token(token: str, env_path: Path | None = None) -> Path:
    path = (env_path or default_env_path()).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"TODOIST_API_TOKEN={token.strip()}\n", encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path


def load_dotenv(path: Path | None = None) -> None:
    env_path = (path or default_env_path()).expanduser()
    if not env_path.exists():
        return
    if os.name == "posix":
        mode = env_path.stat().st_mode
        if mode & (stat.S_IRWXG | stat.S_IRWXO):
            raise ConfigError(f"Refusing to load token file with group/other permissions: {env_path}")
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_todoist_token() -> str:
    load_dotenv()
    return os.environ.get("TODOIST_API_TOKEN", "").strip() or os.environ.get("TODOIST_API_KEY", "").strip()
