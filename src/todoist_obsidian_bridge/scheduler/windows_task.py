from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from .core import Schedule


TASK_NAME = "todoist-to-obsidian"


def render_task_xml(command: list[str], config_path: Path, schedule: Schedule) -> str:
    executable = command[0]
    arguments = " ".join(command[1:] + ["run", "--config", str(config_path)])
    if schedule.kind == "interval":
        trigger = f"""<TimeTrigger>
      <Repetition>
        <Interval>PT{schedule.seconds // 60}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2026-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>"""
    else:
        trigger = f"""<CalendarTrigger>
      <StartBoundary>2026-01-01T{schedule.value}:00</StartBoundary>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
      <Enabled>true</Enabled>
    </CalendarTrigger>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    {trigger}
  </Triggers>
  <Principals>
    <Principal id="Author"><LogonType>InteractiveToken</LogonType></Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(executable)}</Command>
      <Arguments>{escape(arguments)}</Arguments>
    </Exec>
  </Actions>
</Task>
"""
