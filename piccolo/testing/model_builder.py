from __future__ import annotations

import datetime
import decimal
import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any, Optional, Union, cast
from uuid import UUID

from piccolo.columns import JSON, JSONB, Array, Column, Email, ForeignKey
from piccolo.custom_types import TableInstance
from piccolo.testing.random_builder import RandomBuilder
from piccolo.utils.sync import run_sync


class ModelBuilder:
    __DEFAULT_MAPPER: dict[type, Callable] = {
        bool: RandomBuilder.next_bool,
        bytes: RandomBuilder.next_bytes,
        datetime.date: RandomBuilder.next_date,
        datetime.datetime: RandomBuilder.next_datetime,
        float: RandomBuilder.next_float,
        decimal.Decimal: RandomBuilder.next_decimal,
        int: RandomBuilder.next_int,
        str: RandomBuilder.next_str,
        datetime.time: RandomBuilder.next_time,
        datetime.timedelta: RandomBuilder.next_timedelta,
        UUID: RandomBuilder.next_uuid,
    }

    @classmethod
    async def build(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> TableInstance:
        pass

    @classmethod
    def build_sync(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> TableInstance:
        pass

    @classmethod
    async def _build(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        minimal: bool = False,
        persist: bool = True,
    ) -> TableInstance:
        pass

    @classmethod
    def _randomize_attribute(cls, column: Column) -> Any:
        pass
