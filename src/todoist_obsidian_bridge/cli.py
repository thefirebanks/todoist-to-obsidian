from __future__ import annotations

import argparse
import getpass
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .config import (
    AppConfig,
    ConfigError,
    FormatConfig,
    ObsidianConfig,
    TodoistConfig,
    get_todoist_token,
    load_config,
    render_config,
    write_config,
    write_env_token,
)
from .formatting import markdown_block
from .obsidian import ObsidianError, append_blocks
from .paths import app_config_dir, app_state_dir, default_config_path, default_env_path, default_state_path
from .routing import resolve_target_and_content
from .scheduler.core import ScheduleError, parse_schedule
from .scheduler.launchd import LABEL as LAUNCHD_LABEL
from .scheduler.launchd import render_plist
from .scheduler.systemd import SERVICE_NAME, TIMER_NAME, render_service, render_timer
from .scheduler.windows_task import TASK_NAME, render_task_xml
from .state import load_state, save_state
from .todoist import TodoistClient, TodoistError


def command_for_scheduler() -> list[str]:
    return [sys.executable, "-m", "todoist_obsidian_bridge"]


def prompt(text: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{text}{suffix}: ").strip()
    return value or default


def prompt_bool(text: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    value = input(f"{text} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "true", "1"}


def collect_aliases() -> dict[str, str]:
    aliases: dict[str, str] = {}
    if not prompt_bool("Add routing aliases now?", False):
        return aliases
    print("Add aliases like `project` -> `Notes/project.md`. Leave alias blank when done.")
    while True:
        alias = input("Alias prefix: ").strip()
        if not alias:
            return aliases
        target = input("Relative note path: ").strip()
        if target:
            aliases[alias] = target


def cmd_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser() if args.config else default_config_path()
    if config_path.exists() and not args.force:
        print(f"Config already exists: {config_path}")
        print("Use --force to overwrite it.")
        return 2

    print("todoist-to-obsidian setup")
    print()
    token = getpass.getpass("Paste your Todoist API token: ").strip()
    if not token:
        print("A Todoist token is required.")
        return 2

    vault_path = Path(prompt("Obsidian vault path")).expanduser()
    default_note = prompt("Default note for uncategorized captures", "Inbox.md")
    project = prompt("Todoist project to import from", "obs")
    label = prompt("Optional Todoist label filter", "")
    close_after_import = prompt_bool("Close Todoist tasks after importing?", True)
    aliases = collect_aliases()

    config = AppConfig(
        todoist=TodoistConfig(project=project, label=label, close_after_import=close_after_import),
        obsidian=ObsidianConfig(vault_path=vault_path, default_note=default_note),
        fmt=FormatConfig(),
        aliases=aliases,
        state_path=default_state_path(),
        config_path=config_path,
    )

    write_config(config, overwrite=args.force)
    env_path = write_env_token(token)
    print()
    print(f"Wrote config: {config_path}")
    print(f"Stored token locally: {env_path}")

    if prompt_bool("Run a dry-run now?", True):
        return cmd_run(argparse.Namespace(config=str(config_path), dry_run=True, no_close=True))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        config = load_config(Path(args.config).expanduser() if args.config else None)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2

    try:
        token = get_todoist_token()
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2
    if not token:
        print(f"Missing Todoist token. Run `todoist-to-obsidian init` or create {default_env_path()}.", file=sys.stderr)
        return 2

    if not config.obsidian.vault_path.exists():
        print(f"Vault path does not exist: {config.obsidian.vault_path}", file=sys.stderr)
        return 2

    client = TodoistClient(token)
    try:
        tasks = client.get_capture_tasks(
            config.todoist.project,
            config.todoist.label,
            config.todoist.filter_query,
        )
    except TodoistError as exc:
        print(exc, file=sys.stderr)
        return 1

    state = load_state(config.state_path)
    imported_ids = set(str(task_id) for task_id in state.get("imported_task_ids", []))
    blocks_by_path: dict[str, list[str]] = {}
    imported_now: list[str] = []
    already_seen: list[str] = []

    for task in tasks:
        task_id = str(task["id"])
        if task_id in imported_ids:
            already_seen.append(task_id)
            continue

        try:
            comments = client.get_comments(task_id) if task.get("note_count", 0) else []
        except TodoistError as exc:
            print(exc, file=sys.stderr)
            return 1

        target_path, routed_content, _alias = resolve_target_and_content(
            str(task.get("content", "")),
            config.aliases,
            config.obsidian.default_note,
        )
        blocks_by_path.setdefault(target_path, []).append(markdown_block(task, comments, routed_content, config.fmt))
        imported_ids.add(task_id)
        imported_now.append(task_id)

    if args.dry_run:
        print(f"Found {len(tasks)} matching Todoist task(s).")
        print(f"Would import {len(imported_now)} new task(s).")
        for target_path, blocks in blocks_by_path.items():
            print(f"\n=== {target_path} ===")
            for block in blocks:
                print("\n---\n")
                print(block)
        return 0

    if blocks_by_path:
        try:
            written_paths, warnings = append_blocks(config.obsidian.vault_path, config.obsidian.default_note, blocks_by_path)
        except ObsidianError as exc:
            print(exc, file=sys.stderr)
            return 1
        for warning in warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        state["imported_task_ids"] = sorted(imported_ids)
        save_state(config.state_path, state)
        imported_count = sum(len(blocks) for blocks in blocks_by_path.values())
        print(f"Imported {imported_count} task(s) into {len(written_paths)} note(s):")
        for written_path in written_paths:
            print(f"- {written_path}")
    else:
        print("No new Todoist capture tasks to import.")

    if config.todoist.close_after_import and not args.no_close:
        for task_id in imported_now + already_seen:
            try:
                client.close_task(task_id)
            except TodoistError as exc:
                print(exc, file=sys.stderr)
                return 1
        if imported_now or already_seen:
            print(f"Closed {len(imported_now) + len(already_seen)} Todoist task(s).")

    return 0


def cmd_config_path(_args: argparse.Namespace) -> int:
    print(default_config_path())
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    try:
        config = load_config(Path(args.config).expanduser() if args.config else None)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(render_config(config), end="")
    return 0


def cmd_schedule_install(args: argparse.Namespace) -> int:
    try:
        schedule = parse_schedule(args.every, args.daily_at)
    except ScheduleError as exc:
        print(exc, file=sys.stderr)
        return 2

    config_path = Path(args.config).expanduser() if args.config else default_config_path()
    command = command_for_scheduler()
    system = platform.system()

    if system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        log_dir = app_state_dir()
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(render_plist(command, config_path, schedule, log_dir), encoding="utf-8")
        if not args.no_enable:
            subprocess.run(["launchctl", "bootout", f"gui/{os_user_id()}/{LAUNCHD_LABEL}"], check=False, capture_output=True)
            subprocess.run(["launchctl", "bootstrap", f"gui/{os_user_id()}", str(plist_path)], check=False)
        print(f"Installed launchd schedule: {plist_path}")
        return 0

    if system == "Linux":
        user_dir = Path.home() / ".config" / "systemd" / "user"
        user_dir.mkdir(parents=True, exist_ok=True)
        service_path = user_dir / SERVICE_NAME
        timer_path = user_dir / TIMER_NAME
        service_path.write_text(render_service(command, config_path), encoding="utf-8")
        timer_path.write_text(render_timer(schedule), encoding="utf-8")
        if not args.no_enable and shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
            subprocess.run(["systemctl", "--user", "enable", "--now", TIMER_NAME], check=False)
        print(f"Installed systemd user timer: {timer_path}")
        return 0

    if system == "Windows":
        task_xml = app_config_dir() / "windows-task.xml"
        task_xml.parent.mkdir(parents=True, exist_ok=True)
        task_xml.write_text(render_task_xml(command, config_path, schedule), encoding="utf-8")
        if not args.no_enable:
            subprocess.run(["schtasks", "/Create", "/TN", TASK_NAME, "/XML", str(task_xml), "/F"], check=False)
        print(f"Prepared Windows scheduled task XML: {task_xml}")
        return 0

    print(f"Unsupported platform for schedule install: {system}", file=sys.stderr)
    return 2


def os_user_id() -> str:
    try:
        import os

        return str(os.getuid())
    except AttributeError:
        return ""


def cmd_schedule_remove(_args: argparse.Namespace) -> int:
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["launchctl", "bootout", f"gui/{os_user_id()}/{LAUNCHD_LABEL}"], check=False)
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        if plist_path.exists():
            plist_path.unlink()
        print("Removed launchd schedule.")
        return 0
    if system == "Linux":
        if shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "disable", "--now", TIMER_NAME], check=False)
        for path in [Path.home() / ".config" / "systemd" / "user" / SERVICE_NAME, Path.home() / ".config" / "systemd" / "user" / TIMER_NAME]:
            if path.exists():
                path.unlink()
        print("Removed systemd user timer.")
        return 0
    if system == "Windows":
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False)
        print("Removed Windows scheduled task.")
        return 0
    print(f"Unsupported platform for schedule remove: {system}", file=sys.stderr)
    return 2


def cmd_schedule_status(_args: argparse.Namespace) -> int:
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["launchctl", "print", f"gui/{os_user_id()}/{LAUNCHD_LABEL}"], check=False)
        return 0
    if system == "Linux" and shutil.which("systemctl"):
        subprocess.run(["systemctl", "--user", "status", TIMER_NAME], check=False)
        return 0
    if system == "Windows":
        subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME], check=False)
        return 0
    print("No supported scheduler status command available.", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todoist-to-obsidian")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create config and store the Todoist token locally.")
    init_parser.add_argument("--config", help="Config path to write.")
    init_parser.add_argument("--force", action="store_true", help="Overwrite an existing config.")
    init_parser.set_defaults(func=cmd_init)

    run_parser = subparsers.add_parser("run", help="Import matching Todoist tasks into Obsidian.")
    run_parser.add_argument("--config", help="Config path.")
    run_parser.add_argument("--dry-run", action="store_true", help="Print what would import without writing or closing tasks.")
    run_parser.add_argument("--no-close", action="store_true", help="Do not close Todoist tasks after importing.")
    run_parser.set_defaults(func=cmd_run)

    config_parser = subparsers.add_parser("config", help="Inspect configuration.")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)
    config_path_parser = config_subparsers.add_parser("path", help="Print the default config path.")
    config_path_parser.set_defaults(func=cmd_config_path)
    config_show_parser = config_subparsers.add_parser("show", help="Print the loaded config without secrets.")
    config_show_parser.add_argument("--config", help="Config path.")
    config_show_parser.set_defaults(func=cmd_config_show)

    schedule_parser = subparsers.add_parser("schedule", help="Manage a platform scheduler.")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command", required=True)
    install_parser = schedule_subparsers.add_parser("install", help="Install a scheduled run.")
    install_parser.add_argument("--config", help="Config path.")
    install_parser.add_argument("--every", help="Interval such as 15m, 1h, 6h, or 24h.")
    install_parser.add_argument("--daily-at", help="Daily local time in 24-hour HH:MM format.")
    install_parser.add_argument("--no-enable", action="store_true", help="Write scheduler files without enabling them.")
    install_parser.set_defaults(func=cmd_schedule_install)
    remove_parser = schedule_subparsers.add_parser("remove", help="Remove the installed schedule.")
    remove_parser.set_defaults(func=cmd_schedule_remove)
    status_parser = schedule_subparsers.add_parser("status", help="Show scheduler status.")
    status_parser.set_defaults(func=cmd_schedule_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
