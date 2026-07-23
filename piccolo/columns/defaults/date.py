from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Union

from .base import Default


class DateOffset(Default):

    def __init__(self, days: int):
        """
        :param days:
            The number of days to offset.
        """
        self.days = days

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


class DateNow(Default):
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


class DateCustom(Default):
    def __init__(
        self,
        year: int,
        month: int,
        day: int,
    ):
        self.day = day
        self.month = month
        self.year = year
        self.date = datetime.date(year=year, month=month, day=day)

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
    def from_date(cls, instance: datetime.date):
        pass


DateArg = Union[
    DateOffset,
    DateCustom,
    DateNow,
    Enum,
    None,
    datetime.date,
    Callable[[], datetime.date],
]


__all__ = ["DateArg", "DateOffset", "DateCustom", "DateNow"]
