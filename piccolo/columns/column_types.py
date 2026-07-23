
from __future__ import annotations

import copy
import decimal
import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    Union,
    cast,
    overload,
)

from typing_extensions import Unpack

from piccolo.columns.base import (
    Column,
    ColumnKwargs,
    ForeignKeyMeta,
    OnDelete,
    OnUpdate,
    ReferencedTable,
)
from piccolo.columns.combination import Where
from piccolo.columns.defaults.date import DateArg, DateCustom, DateNow
from piccolo.columns.defaults.interval import IntervalArg, IntervalCustom
from piccolo.columns.defaults.time import TimeArg, TimeCustom, TimeNow
from piccolo.columns.defaults.timestamp import (
    TimestampArg,
    TimestampCustom,
    TimestampNow,
)
from piccolo.columns.defaults.timestamptz import (
    TimestamptzArg,
    TimestamptzCustom,
    TimestamptzNow,
)
from piccolo.columns.defaults.uuid import UUID4, UUIDArg
from piccolo.columns.operators.comparison import (
    ArrayAll,
    ArrayAny,
    ArrayNotAny,
)
from piccolo.columns.operators.string import Concat
from piccolo.columns.reference import LazyTableReference
from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json
from piccolo.utils.warnings import colored_warning

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import ColumnMeta
    from piccolo.query.functions.array import ArrayItemType, ArrayType
    from piccolo.query.operators.json import (
        GetChildElement,
        GetElementFromPath,
    )
    from piccolo.table import Table




class ConcatDelegate:

    def get_querystring(
        self,
        column: Column,
        value: Union[str, Column, QueryString],
        reverse: bool = False,
    ) -> QueryString:
        pass


class MathDelegate:

    def get_querystring(
        self,
        column_name: str,
        operator: Literal["+", "-", "/", "*"],
        value: Union[int, float, Integer],
        reverse: bool = False,
    ) -> QueryString:
        pass


class TimedeltaDelegate:

    postgres_attr_map: dict[str, str] = {
        "days": "DAYS",
        "seconds": "SECONDS",
        "microseconds": "MICROSECONDS",
    }

    def get_postgres_interval_string(self, interval: timedelta) -> str:
        pass

    def get_sqlite_interval_string(self, interval: timedelta) -> str:
        pass

    def get_querystring(
        self,
        column: Column,
        operator: Literal["+", "-"],
        value: timedelta,
        engine_type: str,
    ) -> QueryString:
        pass




class Varchar(Column):

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(
        self,
        length: Optional[int] = 255,
        default: Union[str, Enum, Callable[[], str], None] = "",
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (str, None))

        self.length = length
        self.default = default
        super().__init__(length=length, default=default, **kwargs)

    @property
    def column_type(self):
        return f"VARCHAR({self.length})" if self.length else "VARCHAR"


    def __add__(self, value: Union[str, Varchar, Text]) -> QueryString:
        return self.concat_delegate.get_querystring(
            column=self,
            value=value,
        )

    def __radd__(self, value: Union[str, Varchar, Text]) -> QueryString:
        return self.concat_delegate.get_querystring(
            column=self,
            value=value,
            reverse=True,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> str: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Varchar: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[str, None]):
        obj.__dict__[self._meta.name] = value


class Email(Varchar):

    pass


class Char(Varchar):

    @property
    def column_type(self):
        return f"CHAR({self.length})" if self.length else "CHAR"


class Secret(Varchar):

    def __init__(self, *args, **kwargs):
        kwargs["secret"] = True
        super().__init__(*args, **kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> str: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Secret: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[str, None]):
        obj.__dict__[self._meta.name] = value


class Text(Column):

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(
        self,
        default: Union[str, Enum, None, Callable[[], str]] = "",
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (str, None))
        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: Union[str, Varchar, Text]) -> QueryString:
        return self.concat_delegate.get_querystring(
            column=self,
            value=value,
        )

    def __radd__(self, value: Union[str, Varchar, Text]) -> QueryString:
        return self.concat_delegate.get_querystring(
            column=self,
            value=value,
            reverse=True,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> str: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Text: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[str, None]):
        obj.__dict__[self._meta.name] = value


class UUID(Column):

    value_type = uuid.UUID

    def __init__(
        self,
        default: UUIDArg = UUID4(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        if default is UUID4:
            default = UUID4()

        self._validate_default(default, UUIDArg.__args__)  # type: ignore

        if default == uuid.uuid4:
            default = UUID4()

        if isinstance(default, str):
            try:
                default = uuid.UUID(default)
            except ValueError as e:
                raise ValueError(
                    "The default is a string, but not a valid uuid."
                ) from e

        self.default = default
        super().__init__(default=default, **kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> uuid.UUID: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> UUID: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[uuid.UUID, None]):
        obj.__dict__[self._meta.name] = value


class Integer(Column):

    math_delegate = MathDelegate()

    def __init__(
        self,
        default: Union[int, Enum, Callable[[], int], None] = 0,
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (int, None))
        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name, operator="+", value=value
        )

    def __radd__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name,
            operator="+",
            value=value,
            reverse=True,
        )

    def __sub__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name, operator="-", value=value
        )

    def __rsub__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name,
            operator="-",
            value=value,
            reverse=True,
        )

    def __mul__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name, operator="*", value=value
        )

    def __rmul__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name,
            operator="*",
            value=value,
            reverse=True,
        )

    def __truediv__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name, operator="/", value=value
        )

    def __rtruediv__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name,
            operator="/",
            value=value,
            reverse=True,
        )

    def __floordiv__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name, operator="/", value=value
        )

    def __rfloordiv__(self, value: Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.db_column_name,
            operator="/",
            value=value,
            reverse=True,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Integer: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value




class BigInt(Integer):

    def _get_column_type(self, engine_type: str):
        if engine_type == "postgres":
            return "BIGINT"
        elif engine_type == "cockroach":
            return "BIGINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")

    @property
    def column_type(self):
        return self._get_column_type(engine_type=self._meta.engine_type)


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> BigInt: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value


class SmallInt(Integer):

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type == "postgres":
            return "SMALLINT"
        elif engine_type == "cockroach":
            return "SMALLINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> SmallInt: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value




DEFAULT = QueryString("DEFAULT")
NULL = QueryString("null")


class Serial(Column):

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type == "postgres":
            return "SERIAL"
        elif engine_type == "cockroach":
            return "INTEGER"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")

    def default(self) -> QueryString:
        engine_type = self._meta.engine_type

        if engine_type == "postgres":
            return DEFAULT
        elif engine_type == "cockroach":
            return QueryString("unique_rowid()")
        elif engine_type == "sqlite":
            return NULL
        raise Exception("Unrecognized engine type")


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Serial: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value


class BigSerial(Serial):

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type == "postgres":
            return "BIGSERIAL"
        elif engine_type == "cockroach":
            return "BIGINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> BigSerial: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value


class PrimaryKey(Serial):
    def __init__(
        self,
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        kwargs.update({"primary_key": True, "index": False})

        colored_warning(
            "`PrimaryKey` is deprecated and will be removed in future "
            "versions. Use `UUID(primary_key=True)` or "
            "`Serial(primary_key=True)` instead. If no primary key column is "
            "specified, Piccolo will automatically add one for you called "
            "`id`.",
            category=DeprecationWarning,
        )

        super().__init__(**kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> int: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> PrimaryKey: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[int, None]):
        obj.__dict__[self._meta.name] = value




class Timestamp(Column):

    value_type = datetime
    timedelta_delegate = TimedeltaDelegate()

    def __init__(
        self,
        default: TimestampArg = TimestampNow(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, TimestampArg.__args__)  # type: ignore

        if isinstance(default, datetime):
            if default.tzinfo is not None:
                raise ValueError(
                    "Timestamp only stores timezone naive datetime objects - "
                    "use Timestamptz instead."
                )
            default = TimestampCustom.from_datetime(default)

        if default == datetime.now:
            default = TimestampNow()

        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="+",
            value=value,
            engine_type=self._meta.engine_type,
        )

    def __radd__(self, value: timedelta) -> QueryString:
        return self.__add__(value)

    def __sub__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="-",
            value=value,
            engine_type=self._meta.engine_type,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> datetime: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Timestamp: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[datetime, None]):
        obj.__dict__[self._meta.name] = value


class Timestamptz(Column):

    value_type = datetime

    tz_aware = True

    timedelta_delegate = TimedeltaDelegate()

    def __init__(
        self,
        default: TimestamptzArg = TimestamptzNow(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(
            default, TimestamptzArg.__args__  # type: ignore
        )

        if isinstance(default, datetime):
            default = TimestamptzCustom.from_datetime(default)

        if default == datetime.now:
            default = TimestamptzNow()

        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="+",
            value=value,
            engine_type=self._meta.engine_type,
        )

    def __radd__(self, value: timedelta) -> QueryString:
        return self.__add__(value)

    def __sub__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="-",
            value=value,
            engine_type=self._meta.engine_type,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> datetime: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Timestamptz: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[datetime, None]):
        obj.__dict__[self._meta.name] = value


class Date(Column):

    value_type = date
    timedelta_delegate = TimedeltaDelegate()

    def __init__(
        self,
        default: DateArg = DateNow(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, DateArg.__args__)  # type: ignore

        if isinstance(default, date):
            default = DateCustom.from_date(default)

        if default == date.today:
            default = DateNow()

        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="+",
            value=value,
            engine_type=self._meta.engine_type,
        )

    def __radd__(self, value: timedelta) -> QueryString:
        return self.__add__(value)

    def __sub__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="-",
            value=value,
            engine_type=self._meta.engine_type,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> date: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Date: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[date, None]):
        obj.__dict__[self._meta.name] = value


class Time(Column):

    value_type = time
    timedelta_delegate = TimedeltaDelegate()

    def __init__(
        self,
        default: TimeArg = TimeNow(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, TimeArg.__args__)  # type: ignore

        if isinstance(default, time):
            default = TimeCustom.from_time(default)

        self.default = default
        super().__init__(default=default, **kwargs)


    def __add__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="+",
            value=value,
            engine_type=self._meta.engine_type,
        )

    def __radd__(self, value: timedelta) -> QueryString:
        return self.__add__(value)

    def __sub__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="-",
            value=value,
            engine_type=self._meta.engine_type,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> time: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Time: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[time, None]):
        obj.__dict__[self._meta.name] = value


class Interval(Column):

    value_type = timedelta
    timedelta_delegate = TimedeltaDelegate()

    def __init__(
        self,
        default: IntervalArg = IntervalCustom(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, IntervalArg.__args__)  # type: ignore

        if isinstance(default, timedelta):
            default = IntervalCustom.from_timedelta(default)

        self.default = default
        super().__init__(default=default, **kwargs)

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type in ("postgres", "cockroach"):
            return "INTERVAL"
        elif engine_type == "sqlite":
            return "SECONDS"
        raise Exception("Unrecognized engine type")


    def __add__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="+",
            value=value,
            engine_type=self._meta.engine_type,
        )

    def __radd__(self, value: timedelta) -> QueryString:
        return self.__add__(value)

    def __sub__(self, value: timedelta) -> QueryString:
        return self.timedelta_delegate.get_querystring(
            column=self,
            operator="-",
            value=value,
            engine_type=self._meta.engine_type,
        )


    @overload
    def __get__(self, obj: Table, objtype=None) -> timedelta: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Interval: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[timedelta, None]):
        obj.__dict__[self._meta.name] = value




class Boolean(Column):

    value_type = bool

    def __init__(
        self,
        default: Union[bool, Enum, Callable[[], bool], None] = False,
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (bool, None))
        self.default = default
        super().__init__(default=default, **kwargs)

    def eq(self, value) -> Where:
        pass

    def ne(self, value) -> Where:
        pass


    @overload
    def __get__(self, obj: Table, objtype=None) -> bool: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Boolean: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[bool, None]):
        obj.__dict__[self._meta.name] = value




class Numeric(Column):

    value_type = decimal.Decimal

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type == "cockroach":
            return "NUMERIC"  # All Numeric is the same for Cockroach.
        if self.digits:
            return f"NUMERIC({self.precision}, {self.scale})"
        else:
            return "NUMERIC"

    @property
    def precision(self) -> Optional[int]:
        pass

    @property
    def scale(self) -> Optional[int]:
        pass

    def __init__(
        self,
        digits: Optional[tuple[int, int]] = None,
        default: Union[
            decimal.Decimal, Enum, Callable[[], decimal.Decimal], None
        ] = decimal.Decimal(0.0),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        if isinstance(digits, tuple):
            if len(digits) != 2:
                raise ValueError(
                    "The `digits` argument should be a tuple of length 2, "
                    "with the first value being the precision, and the second "
                    "value being the scale."
                )
        elif digits is not None:
            raise ValueError("The digits argument should be a tuple.")

        self._validate_default(default, (decimal.Decimal, None))

        self.default = default
        self.digits = digits
        super().__init__(default=default, digits=digits, **kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> decimal.Decimal: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Numeric: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[decimal.Decimal, None]):
        obj.__dict__[self._meta.name] = value


class Decimal(Numeric):


    @overload
    def __get__(self, obj: Table, objtype=None) -> decimal.Decimal: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Decimal: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[decimal.Decimal, None]):
        obj.__dict__[self._meta.name] = value


class Real(Column):

    value_type = float

    def __init__(
        self,
        default: Union[float, Enum, Callable[[], float], None] = 0.0,
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        if isinstance(default, int):
            default = float(default)

        self._validate_default(default, (float, None))
        self.default = default
        super().__init__(default=default, **kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> float: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Real: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[float, None]):
        obj.__dict__[self._meta.name] = value


class Float(Real):


    @overload
    def __get__(self, obj: Table, objtype=None) -> float: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Float: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[float, None]):
        obj.__dict__[self._meta.name] = value


class DoublePrecision(Real):

    @property
    def column_type(self):
        return "DOUBLE PRECISION"


    @overload
    def __get__(self, obj: Table, objtype=None) -> float: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> DoublePrecision: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[float, None]):
        obj.__dict__[self._meta.name] = value




@dataclass
class ForeignKeySetupResponse:
    is_lazy: bool


class ForeignKey(Column, Generic[ReferencedTable]):

    _foreign_key_meta: ForeignKeyMeta

    @property
    def column_type(self):
        """
        A ``ForeignKey`` column needs to have the same type as the primary key
        column of the table being referenced.
        """
        target_column = self._foreign_key_meta.resolved_target_column

        if isinstance(target_column, BigSerial):
            return BigInt()._get_column_type(
                engine_type=self._meta.engine_type
            )
        elif isinstance(target_column, Serial):
            return Integer().column_type
        else:
            return target_column.column_type

    @property
    def value_type(self):
        """
        The value type matches that of the primary key being referenced.
        """
        target_column = self._foreign_key_meta.resolved_target_column
        return target_column.value_type

    @overload
    def __init__(
        self,
        references: type[ReferencedTable],
        default: Any = None,
        null: bool = True,
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        target_column: Union[str, Column, None] = None,
        **kwargs,
    ) -> None: ...

    @overload
    def __init__(
        self,
        references: LazyTableReference,
        default: Any = None,
        null: bool = True,
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        target_column: Union[str, Column, None] = None,
        **kwargs,
    ) -> None: ...

    @overload
    def __init__(
        self,
        references: str,
        default: Any = None,
        null: bool = True,
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        target_column: Union[str, Column, None] = None,
        **kwargs,
    ) -> None: ...

    def __init__(
        self,
        references: Union[type[ReferencedTable], LazyTableReference, str],
        default: Any = None,
        null: bool = True,
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        target_column: Union[str, Column, None] = None,
        **kwargs,
    ) -> None:
        from piccolo.table import Table

        if inspect.isclass(references):
            if issubclass(references, Table):
                if isinstance(references._meta.primary_key, Serial):
                    Integer(default=default, null=null)
                else:
                    references._meta.primary_key.__class__(
                        default=default, null=null
                    )

        self.default = default

        kwargs.update(
            {
                "references": references,
                "on_delete": on_delete,
                "on_update": on_update,
                "null": null,
                "target_column": target_column,
            }
        )

        super().__init__(**kwargs)

        self._foreign_key_meta = ForeignKeyMeta(
            references=Table if isinstance(references, str) else references,
            on_delete=on_delete,
            on_update=on_update,
            target_column=target_column,
        )

    def _setup(self, table_class: type[Table]) -> ForeignKeySetupResponse:
        """
        This is called by the ``TableMetaclass``. A ``ForeignKey`` column can
        only be completely setup once it's parent ``Table`` is known.

        :param table_class:
            The parent ``Table`` class for this column.

        """
        from piccolo.table import Table

        params = self._meta.params
        references = params["references"]

        if isinstance(references, str):
            if references == "self":
                references = table_class
            else:
                if "." in references:
                    if references.startswith("."):
                        raise ValueError("Relative imports aren't allowed")

                    module_path, table_class_name = references.rsplit(
                        ".", maxsplit=1
                    )
                else:
                    table_class_name = references
                    module_path = table_class.__module__

                references = LazyTableReference(
                    table_class_name=table_class_name,
                    module_path=module_path,
                )

        is_lazy = isinstance(references, LazyTableReference)
        is_table_class = inspect.isclass(references) and issubclass(
            references, Table
        )

        if is_lazy or is_table_class:
            self._foreign_key_meta.references = references
        else:
            raise ValueError(
                "Error - ``references`` must be a ``Table`` subclass, or "
                "a ``LazyTableReference`` instance."
            )

        if is_table_class:
            cast(type[Table], references)._meta._foreign_key_references.append(
                self
            )

            self.set_proxy_columns()

        return ForeignKeySetupResponse(is_lazy=is_lazy)

    def copy(self) -> ForeignKey:
        column: ForeignKey = copy.copy(self)
        column._meta = self._meta.copy()
        column._foreign_key_meta = self._foreign_key_meta.copy()
        return column

    def all_columns(
        self, exclude: Optional[list[Union[Column, str]]] = None
    ) -> list[Column]:
        """
        Allow a user to access all of the columns on the related table. This is
        intended for use with ``select`` queries, and saves the user from
        typing out all of the columns by hand.

        For example:

        .. code-block:: python

            await Band.select(Band.name, Band.manager.all_columns())

            # Equivalent to:
            await Band.select(
                Band.name,
                Band.manager.id,
                Band.manager.name
            )

        To exclude certain columns:

        .. code-block:: python

            await Band.select(
                Band.name,
                Band.manager.all_columns(
                    exclude=[Band.manager.id]
                )
            )

        :param exclude:
            Columns to exclude - can be the name of a column, or a column
            instance. For example ``['id']`` or ``[Band.manager.id]``.

        """
        if exclude is None:
            exclude = []
        _fk_meta = object.__getattribute__(self, "_foreign_key_meta")

        excluded_column_names = [
            i._meta.name if isinstance(i, Column) else i for i in exclude
        ]

        return [
            getattr(self, column._meta.name)
            for column in _fk_meta.resolved_references._meta.columns
            if column._meta.name not in excluded_column_names
        ]

    def reverse(self) -> ForeignKey:
        """
        If there's a unique foreign key, this function reverses it.

        .. code-block:: python

            class Band(Table):
                name = Varchar()

            class FanClub(Table):
                band = ForeignKey(Band, unique=True)
                address = Text()

            class Treasurer(Table):
                fan_club = ForeignKey(FanClub, unique=True)
                name = Varchar()

        It's helpful with ``get_related``, for example:

        .. code-block:: python

            >>> band = await Band.objects().first()
            >>> await band.get_related(FanClub.band.reverse())
            <Fan Club: 1>

        It works multiple levels deep:

        .. code-block:: python

            >>> await band.get_related(Treasurer.fan_club._.band.reverse())
            <Treasurer: 1>

        """
        if not self._meta.unique or any(
            not i._meta.unique for i in self._meta.call_chain
        ):
            raise ValueError("Only reverse unique foreign keys.")

        foreign_keys = [*self._meta.call_chain, self]

        root_foreign_key = foreign_keys[0]
        target_column = (
            root_foreign_key._foreign_key_meta.resolved_target_column
        )
        foreign_key = target_column.join_on(root_foreign_key)

        call_chain = []
        for fk in reversed(foreign_keys[1:]):
            target_column = fk._foreign_key_meta.resolved_target_column
            call_chain.append(target_column.join_on(fk))

        foreign_key._meta.call_chain = call_chain

        return foreign_key

    def all_related(
        self, exclude: Optional[list[Union[ForeignKey, str]]] = None
    ) -> list[ForeignKey]:
        pass

    def set_proxy_columns(self) -> None:
        """
        In order to allow a fluent interface, where tables can be traversed
        using ForeignKeys (e.g. ``Band.manager.name``), we add attributes to
        the ``ForeignKey`` column for each column in the table being pointed
        to.
        """
        _fk_meta = object.__getattribute__(self, "_foreign_key_meta")
        for column in _fk_meta.resolved_references._meta.columns:
            _column: Column = column.copy()
            setattr(self, _column._meta.name, _column)
            _fk_meta.proxy_columns.append(_column)

    @property
    def _(self) -> type[ReferencedTable]:
        pass

    def __getattribute__(self, name: str) -> Union[Column, Any]:
        """
        Returns attributes unmodified unless they're Column instances, in which
        case a copy is returned with an updated call_chain (which records the
        joins required).
        """
        if not name.startswith("_") and name not in dir(self):
            try:
                _foreign_key_meta = object.__getattribute__(
                    self, "_foreign_key_meta"
                )
            except AttributeError:
                pass
            else:
                if _foreign_key_meta.proxy_columns == [] and isinstance(
                    _foreign_key_meta.references, LazyTableReference
                ):
                    object.__getattribute__(self, "set_proxy_columns")()

        value = object.__getattribute__(self, name)

        if name.startswith("_"):
            return value

        foreignkey_class: type[ForeignKey] = object.__getattribute__(
            self, "__class__"
        )

        if isinstance(value, foreignkey_class):  # i.e. a ForeignKey
            new_column = value.copy()
            new_column._meta.call_chain.append(self)

            if len(new_column._meta.call_chain) >= 10:
                raise Exception("Call chain too long!")

            foreign_key_meta: ForeignKeyMeta = object.__getattribute__(
                new_column, "_foreign_key_meta"
            )

            for proxy_column in foreign_key_meta.proxy_columns:
                try:
                    delattr(new_column, proxy_column._meta.name)
                except Exception:
                    pass

            foreign_key_meta.proxy_columns = []

            for (
                column
            ) in value._foreign_key_meta.resolved_references._meta.columns:
                _column: Column = column.copy()
                _column._meta.call_chain = list(new_column._meta.call_chain)
                setattr(new_column, _column._meta.name, _column)
                foreign_key_meta.proxy_columns.append(_column)

            return new_column
        elif issubclass(type(value), Column):
            new_column = value.copy()

            column_meta: ColumnMeta = object.__getattribute__(self, "_meta")

            new_column._meta.call_chain = column_meta.call_chain.copy()

            new_column._meta.call_chain.append(self)
            return new_column
        else:
            return value


    @overload
    def __get__(self, obj: Table, objtype=None) -> Any: ...

    @overload
    def __get__(
        self, obj: None, objtype=None
    ) -> ForeignKey[ReferencedTable]: ...

    @overload
    def __get__(self, obj: Any, objtype=None) -> Any: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Any):
        obj.__dict__[self._meta.name] = value




class JSON(Column):

    value_type = str

    def __init__(
        self,
        default: Union[
            str,
            list,
            dict,
            Callable[[], Union[str, list, dict]],
            None,
        ] = "{}",
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (str, list, dict, None))

        if isinstance(default, (list, dict)):
            default = dump_json(default)

        self.default = default
        super().__init__(default=default, **kwargs)

        self.json_operator: Optional[str] = None

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type == "cockroach":
            return "JSONB"  # Cockroach is always JSONB.
        else:
            return "JSON"


    def arrow(self, key: Union[str, int, QueryString]) -> GetChildElement:
        pass

    def __getitem__(
        self, value: Union[str, int, QueryString]
    ) -> GetChildElement:
        """
        A shortcut for the ``arrow`` method, used for retrieving a child
        element.

        For example:

        .. code-block:: python

            >>> await RecordingStudio.select(
            ...     RecordingStudio.facilities["restaurant"]
            ... )

        """
        return self.arrow(key=value)

    def from_path(
        self,
        path: list[Union[str, int]],
    ) -> GetElementFromPath:
        pass


    @overload
    def __get__(self, obj: Table, objtype=None) -> str: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> JSON: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[str, dict]):
        obj.__dict__[self._meta.name] = value


class JSONB(JSON):

    @property
    def column_type(self):
        return "JSONB"  # Must be defined, we override column_type() in JSON()


    @overload
    def __get__(self, obj: Table, objtype=None) -> str: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> JSONB: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: Union[str, dict]):
        obj.__dict__[self._meta.name] = value




class Bytea(Column):

    value_type = bytes

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type in ("postgres", "cockroach"):
            return "BYTEA"
        elif engine_type == "sqlite":
            return "BLOB"
        raise Exception("Unrecognized engine type")

    def __init__(
        self,
        default: Union[
            bytes,
            bytearray,
            Enum,
            Callable[[], bytes],
            Callable[[], bytearray],
            None,
        ] = b"",
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        self._validate_default(default, (bytes, bytearray, None))

        if isinstance(default, bytearray):
            default = bytes(default)

        self.default = default
        super().__init__(default=default, **kwargs)


    @overload
    def __get__(self, obj: Table, objtype=None) -> bytes: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Bytea: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: bytes):
        obj.__dict__[self._meta.name] = value


class Blob(Bytea):


    @overload
    def __get__(self, obj: Table, objtype=None) -> bytes: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Blob: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: bytes):
        obj.__dict__[self._meta.name] = value




class ListProxy:

    def __call__(self):
        return []

    def __repr__(self):
        return "list"


class Array(Column):

    value_type = list

    def __init__(
        self,
        base_column: Column,
        default: Union[list, Enum, Callable[[], list], None] = ListProxy(),
        **kwargs: Unpack[ColumnKwargs],
    ) -> None:
        if isinstance(base_column, ForeignKey):
            raise ValueError("Arrays of ForeignKeys aren't allowed.")

        if isinstance(default, ListProxy):
            default = list

        self._validate_default(default, (list, None))

        choices = kwargs.get("choices")
        if choices is not None:
            self._validate_choices(
                choices, allowed_type=base_column.value_type
            )
            self._validated_choices = True

        base_column._meta._name = base_column.__class__.__name__

        self.base_column = base_column
        self.default = default
        self.index: Optional[int] = None
        super().__init__(default=default, base_column=base_column, **kwargs)

    @property
    def column_type(self):
        engine_type = self._meta.engine_type
        if engine_type in ("postgres", "cockroach"):
            return f"{self.base_column.column_type}[]"
        elif engine_type == "sqlite":
            inner_column = self._get_inner_column()
            return (
                f"ARRAY_{inner_column.column_type}"
                if isinstance(
                    inner_column, (Date, Timestamp, Timestamptz, Time)
                )
                else "ARRAY"
            )
        raise Exception("Unrecognized engine type")

    def _setup_base_column(self, table_class: type[Table]):
        """
        Called from the ``Table.__init_subclass__`` - makes sure
        that the ``base_column`` has a reference to the parent table.
        """
        self.base_column._meta._table = table_class
        if isinstance(self.base_column, Array):
            self.base_column._setup_base_column(table_class=table_class)

    def _get_dimensions(self, start: int = 0) -> int:
        """
        A helper function to get the number of dimensions for the array. For
        example::

            >>> Array(Varchar())._get_dimensions()
            1

            >>> Array(Array(Varchar()))._get_dimensions()
            2

        :param start:
            Ignore this - it's just used for  calling this method recursively.

        """
        if isinstance(self.base_column, Array):
            return self.base_column._get_dimensions(start=start + 1)
        else:
            return start + 1

    def _get_inner_column(self) -> Column:
        """
        A helper function to get the innermost ``Column`` for the array. For
        example::

            >>> Array(Varchar())._get_inner_column()
            Varchar

            >>> Array(Array(Varchar()))._get_inner_column()
            Varchar

        """
        if isinstance(self.base_column, Array):
            return self.base_column._get_inner_column()
        else:
            return self.base_column

    def _get_inner_value_type(self) -> type:
        pass

    def __getitem__(self, value: int) -> Array:
        """
        Allows queries which retrieve an item from the array. The index starts
        with 0 for the first value. If you were to write the SQL by hand, the
        first index would be 1 instead (see `Postgres array docs <https://www.postgresql.org/docs/current/arrays.html>`_).

        However, we keep the first index as 0 to fit better with Python.

        For example:

        .. code-block:: python

            >>> await Ticket.select(Ticket.seat_numbers[0]).first()
            {'seat_numbers': 325}


        """  # noqa: E501
        engine_type = self._meta.engine_type
        if engine_type != "postgres" and engine_type != "cockroach":
            raise ValueError(
                "Only Postgres and Cockroach support array indexing."
            )

        if isinstance(value, int):
            if value < 0:
                raise ValueError("Only positive integers are allowed.")

            instance = cast(Array, self.copy())

            instance.index = value + 1
            return instance
        else:
            raise ValueError("Only integers can be used for indexing.")

    def get_select_string(
        self, engine_type: str, with_alias=True
    ) -> QueryString:
        pass

    def any(self, value: Any) -> Where:
        pass

    def not_any(self, value: Any) -> Where:
        pass

    def all(self, value: Any) -> Where:
        pass

    def cat(self, value: ArrayType) -> QueryString:
        pass

    def remove(self, value: ArrayItemType) -> QueryString:
        pass

    def prepend(self, value: ArrayItemType) -> QueryString:
        pass

    def append(self, value: ArrayItemType) -> QueryString:
        """
        A convenient way of accessing the
        :class:`ArrayAppend <piccolo.query.functions.array.ArrayAppend>`
        function.

        Used in an ``update`` query to append an item to an array.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.append(1000)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        from piccolo.query.functions.array import ArrayAppend

        return ArrayAppend(array=self, value=value)

    def replace(
        self, old_value: ArrayItemType, new_value: ArrayItemType
    ) -> QueryString:
        """
        A convenient way of accessing the
        :class:`ArrayReplace <piccolo.query.functions.array.ArrayReplace>`
        function.

        Used in an ``update`` query to replace each array item
        equal to the given value with a new value.

        .. code-block:: python

            >>> await Ticket.update({
            ...     Ticket.seat_numbers: Ticket.seat_numbers.replace(1000, 500)
            ... }).where(Ticket.id == 1)

        .. note:: Postgres / CockroachDB only

        """
        from piccolo.query.functions.array import ArrayReplace

        return ArrayReplace(self, old_value=old_value, new_value=new_value)

    def __add__(self, value: ArrayType) -> QueryString:
        return self.cat(value)

    def __radd__(self, value: ArrayType) -> QueryString:
        from piccolo.query.functions.array import ArrayCat

        return ArrayCat(array_1=value, array_2=self)


    @overload
    def __get__(self, obj: Table, objtype=None) -> list[Any]: ...

    @overload
    def __get__(self, obj: None, objtype=None) -> Array: ...

    def __get__(self, obj, objtype=None):
        return obj.__dict__[self._meta.name] if obj else self

    def __set__(self, obj, value: list[Any]):
        obj.__dict__[self._meta.name] = value
