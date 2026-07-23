from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Union

from .base import Default


class TimestampOffset(Default):
    def __init__(
        self, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0
    ):
        self.days = days
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


class TimestampNow(Default):

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


class TimestampCustom(Default):
    def __init__(
        self,
        year: int = 2000,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
    ):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.microsecond = microsecond

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
        )

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
    def from_datetime(cls, instance: datetime.datetime):  # type: ignore
        pass




class DatetimeDefault:
    now = TimestampNow()



TimestampArg = Union[
    TimestampCustom,
    TimestampNow,
    TimestampOffset,
    Enum,
    None,
    datetime.datetime,
    DatetimeDefault,
    Callable[[], datetime.datetime],
]


__all__ = [
    "TimestampArg",
    "TimestampCustom",
    "TimestampNow",
    "TimestampOffset",
]
