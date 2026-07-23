import datetime
import decimal
import enum
import random
import string
import uuid
from typing import Any, Sequence


class RandomBuilder:
    @classmethod
    def next_bool(cls) -> bool:
        pass

    @classmethod
    def next_bytes(cls, length: int = 8) -> bytes:
        pass

    @classmethod
    def next_date(cls) -> datetime.date:
        pass

    @classmethod
    def next_datetime(cls, tz_aware: bool = False) -> datetime.datetime:
        pass

    @classmethod
    def next_enum(cls, e: type[enum.Enum]) -> Any:
        pass

    @classmethod
    def next_float(
        cls, minimum: int = 0, maximum: int = 2147483647, scale: int = 5
    ) -> float:
        pass

    @classmethod
    def next_decimal(
        cls, precision: int = 4, scale: int = 2
    ) -> decimal.Decimal:
        pass

    @classmethod
    def next_int(cls, minimum: int = 0, maximum: int = 2147483647) -> int:
        pass

    @classmethod
    def next_str(
        cls, length: int = 16, choices: Sequence = string.ascii_letters
    ) -> str:
        pass

    @classmethod
    def next_email(cls) -> str:
        pass

    @classmethod
    def next_time(cls) -> datetime.time:
        pass

    @classmethod
    def next_timedelta(cls) -> datetime.timedelta:
        pass

    @classmethod
    def next_uuid(cls) -> uuid.UUID:
        pass
