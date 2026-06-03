from __future__ import annotations

import re
from dataclasses import dataclass


class ScheduleError(RuntimeError):
    pass


@dataclass(frozen=True)
class Schedule:
    kind: str
    value: str

    @property
    def seconds(self) -> int:
        if self.kind != "interval":
            raise ScheduleError("Only interval schedules have seconds.")
        amount = int(self.value[:-1])
        unit = self.value[-1]
        return amount * 60 if unit == "m" else amount * 3600


def parse_schedule(every: str | None = None, daily_at: str | None = None) -> Schedule:
    if bool(every) == bool(daily_at):
        raise ScheduleError("Specify exactly one of --every or --daily-at.")
    if every:
        normalized = every.strip().lower()
        if not re.fullmatch(r"[1-9][0-9]*[mh]", normalized):
            raise ScheduleError("Interval must look like 15m, 1h, 6h, or 24h.")
        return Schedule("interval", normalized)
    assert daily_at is not None
    normalized = daily_at.strip()
    if not re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", normalized):
        raise ScheduleError("Daily time must use 24-hour HH:MM format, such as 21:30.")
    return Schedule("daily", normalized)
