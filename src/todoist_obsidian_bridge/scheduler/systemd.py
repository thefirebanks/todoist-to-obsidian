from __future__ import annotations

from pathlib import Path

from .core import Schedule


SERVICE_NAME = "todoist-to-obsidian.service"
TIMER_NAME = "todoist-to-obsidian.timer"


def render_service(command: list[str], config_path: Path) -> str:
    exec_start = " ".join(command + ["run", "--config", str(config_path)])
    return f"""[Unit]
Description=todoist-to-obsidian

[Service]
Type=oneshot
ExecStart={exec_start}
"""


def render_timer(schedule: Schedule) -> str:
    if schedule.kind == "interval":
        trigger = f"OnUnitActiveSec={schedule.value}"
    else:
        trigger = f"OnCalendar=*-*-* {schedule.value}:00"
    return f"""[Unit]
Description=Run todoist-to-obsidian

[Timer]
OnBootSec=5m
{trigger}
Persistent=true

[Install]
WantedBy=timers.target
"""
