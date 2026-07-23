from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Union

from .timestamp import TimestampCustom, TimestampNow, TimestampOffset


class TimestamptzOffset(TimestampOffset):
    @property
    def cockroach(self):
        pass

    def python(self):
        pass


class TimestamptzNow(TimestampNow):

    @property
    def cockroach(self):
        pass

    def python(self):
        pass


class TimestamptzCustom(TimestampCustom):
    @property
    def cockroach(self):
        pass

    @property
    def datetime(self):
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.minute,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=datetime.timezone.utc,
        )

    @classmethod
    def from_datetime(cls, instance: datetime.datetime):  # type: ignore
        pass


TimestamptzArg = Union[
    TimestamptzCustom,
    TimestamptzNow,
    TimestamptzOffset,
    Enum,
    None,
    datetime.datetime,
    Callable[[], datetime.datetime],
]


__all__ = [
    "TimestamptzArg",
    "TimestamptzCustom",
    "TimestamptzNow",
    "TimestamptzOffset",
]
