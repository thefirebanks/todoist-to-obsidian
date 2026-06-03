from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .core import Schedule


LABEL = "com.todoist-to-obsidian.run"


def render_plist(command: list[str], config_path: Path, schedule: Schedule, log_dir: Path) -> str:
    args = command + ["run", "--config", str(config_path)]
    arg_xml = "\n".join(f"    <string>{escape(arg)}</string>" for arg in args)
    if schedule.kind == "interval":
        schedule_xml = f"""  <key>StartInterval</key>
  <integer>{schedule.seconds}</integer>"""
    else:
        hour, minute = schedule.value.split(":")
        schedule_xml = f"""  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{int(hour)}</integer>
    <key>Minute</key>
    <integer>{int(minute)}</integer>
  </dict>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
{arg_xml}
  </array>
{schedule_xml}
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{escape(str(log_dir / "run.out.log"))}</string>
  <key>StandardErrorPath</key>
  <string>{escape(str(log_dir / "run.err.log"))}</string>
</dict>
</plist>
"""
