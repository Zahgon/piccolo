from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Union

from .base import Default


class TimeOffset(Default):
    def __init__(self, hours: int, minutes: int, seconds: int):
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    @property
    def postgres(self):
        pass

    @property
    def cockroach(self):
        pass

    @property
    def sqlite(self):
        pass

    def python(self):
        pass


class TimeNow(Default):
    @property
    def postgres(self):
        pass

    @property
    def cockroach(self):
        pass

    @property
    def sqlite(self):
        pass

    def python(self):
        pass


class TimeCustom(Default):
    def __init__(self, hour: int, minute: int, second: int):
        self.hour = hour
        self.minute = minute
        self.second = second
        self.time = datetime.time(hour=hour, minute=minute, second=second)

    @property
    def postgres(self):
        pass

    @property
    def cockroach(self):
        pass

    @property
    def sqlite(self):
        pass

    def python(self):
        pass

    @classmethod
    def from_time(cls, instance: datetime.time):
        pass


TimeArg = Union[
    TimeCustom,
    TimeNow,
    TimeOffset,
    Enum,
    None,
    datetime.time,
    Callable[[], datetime.time],
]


__all__ = ["TimeArg", "TimeCustom", "TimeNow", "TimeOffset"]
