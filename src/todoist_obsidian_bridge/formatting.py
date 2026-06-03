from __future__ import annotations

import datetime as dt
from typing import Any

from .config import FormatConfig


def format_human_long(value: dt.datetime) -> str:
    hour = value.hour % 12 or 12
    suffix = "AM" if value.hour < 12 else "PM"
    return f"{value.strftime('%A')}, {value.strftime('%B')} {value.day}, {value.year} {hour}:{value.minute:02d} {suffix}"


def parse_todoist_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def heading_time(task: dict[str, Any], fmt: FormatConfig, timezone: dt.tzinfo | None = None) -> str:
    source = fmt.heading_time_source
    parsed = parse_todoist_time(str(task.get("created_at", "") or "")) if source == "todoist_created_at" else None
    value = parsed or dt.datetime.now().astimezone()
    local_value = value.astimezone(timezone) if timezone else value.astimezone()
    if fmt.heading_format == "human_long":
        return format_human_long(local_value)
    return local_value.strftime(fmt.heading_format)


def markdown_block(task: dict[str, Any], comments: list[dict[str, Any]], content: str, fmt: FormatConfig) -> str:
    description = str(task.get("description", "") or "").strip()
    url = str(task.get("url", "") or "").strip()
    labels = task.get("labels") or []

    lines = [f"## {heading_time(task, fmt)}", "", content]

    if description:
        lines.extend(["", description])

    for comment in comments:
        comment_body = str(comment.get("content", "") or "").strip()
        if comment_body:
            lines.extend(["", comment_body])

    meta = []
    if fmt.include_source:
        meta.append(f"Source: [Todoist]({url})" if url else "Source: Todoist")
    if fmt.include_labels and labels:
        meta.append("Labels: " + ", ".join(str(label) for label in labels))
    if meta:
        lines.extend(["", "_{}._".format(" | ".join(meta))])
    lines.append("")
    return "\n".join(lines)
