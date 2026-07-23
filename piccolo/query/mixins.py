from __future__ import annotations

import asyncio
import collections.abc
import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from piccolo.columns import And, Column, Or, Where
from piccolo.columns.column_types import ForeignKey
from piccolo.columns.combination import WhereRaw
from piccolo.custom_types import Combinable
from piccolo.querystring import QueryString
from piccolo.utils.list import flatten
from piccolo.utils.sql_values import convert_to_sql_value

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.querystring import Selectable
    from piccolo.table import Table  # noqa


class DistinctOnError(ValueError):

    pass


@dataclass
class Distinct:
    __slots__ = ("enabled", "on")

    enabled: bool
    on: Optional[Sequence[Column]]

    @property
    def querystring(self) -> QueryString:
        pass

    def validate_on(self, order_by: OrderBy):
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()

    def copy(self) -> Distinct:
        return self.__class__(enabled=self.enabled, on=self.on)


@dataclass
class Limit:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if not isinstance(self.number, int):
            raise TypeError("Limit must be an integer")

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()

    def copy(self) -> Limit:
        return self.__class__(number=self.number)


@dataclass
class AsOf:
    __slots__ = ("interval",)

    interval: str

    def __post_init__(self):
        if not isinstance(self.interval, str):
            raise TypeError("As Of must be a string. Example: '-1s'")

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class Offset:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if not isinstance(self.number, int):
            raise TypeError("Offset must be an integer")

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()


class OrderByRaw(QueryString):

    pass


@dataclass
class OrderByItem:
    __slots__ = ("columns", "ascending")

    columns: Sequence[Union[Column, QueryString]]
    ascending: bool


@dataclass
class OrderBy:
    order_by_items: list[OrderByItem] = field(default_factory=list)

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class Returning:
    __slots__ = ("columns",)

    columns: list[Column]

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class Output:
    as_json: bool = False
    as_list: bool = False
    as_objects: bool = False
    load_json: bool = False
    nested: bool = False

    def copy(self) -> Output:
        return self.__class__(
            as_json=self.as_json,
            as_list=self.as_list,
            as_objects=self.as_objects,
            load_json=self.load_json,
            nested=self.nested,
        )


class CallbackType(Enum):
    success = auto()


@dataclass
class Callback:
    kind: CallbackType
    target: Callable


@dataclass
class WhereDelegate:
    _where: Optional[Combinable] = None
    _where_columns: list[Column] = field(default_factory=list)

    def get_where_columns(self):
        pass

    def _extract_columns(self, combinable: Combinable):
        pass

    def where(self, *where: Union[Combinable, QueryString]):
        for arg in where:
            if isinstance(arg, bool):
                raise ValueError(
                    "A boolean value has been passed in to a where clause. "
                    "This is probably a mistake. For example "
                    "`.where(MyTable.some_column is None)` instead of "
                    "`.where(MyTable.some_column.is_null())`."
                )

            if isinstance(arg, QueryString):
                arg = WhereRaw(arg.template, *arg.args)

            self._where = And(self._where, arg) if self._where else arg


@dataclass
class OrderByDelegate:
    _order_by: OrderBy = field(default_factory=OrderBy)

    def get_order_by_columns(self) -> list[Column]:
        pass

    def order_by(self, *columns: Union[Column, QueryString], ascending=True):
        if len(columns) < 1:
            raise ValueError("At least one column must be passed to order_by.")

        self._order_by.order_by_items.append(
            OrderByItem(columns=columns, ascending=ascending)
        )


@dataclass
class LimitDelegate:
    _limit: Optional[Limit] = None
    _first: bool = False

    def limit(self, number: int):
        self._limit = Limit(number)

    def copy(self) -> LimitDelegate:
        _limit = self._limit.copy() if self._limit is not None else None
        return self.__class__(_limit=_limit, _first=self._first)


@dataclass
class AsOfDelegate:

    _as_of: Optional[AsOf] = None

    def as_of(self, interval: str = "-1s"):
        pass


@dataclass
class DistinctDelegate:
    _distinct: Distinct = field(
        default_factory=lambda: Distinct(enabled=False, on=None)
    )

    def distinct(self, enabled: bool, on: Optional[Sequence[Column]] = None):
        pass


@dataclass
class ReturningDelegate:
    _returning: Optional[Returning] = None

    def returning(self, columns: Sequence[Column]):
        self._returning = Returning(columns=list(columns))


@dataclass
class CountDelegate:
    _count: bool = False

    def count(self):
        pass


@dataclass
class AddDelegate:
    _add: list[Table] = field(default_factory=list)

    def add(self, *instances: Table, table_class: type[Table]):
        for instance in instances:
            if not isinstance(instance, table_class):
                raise TypeError("Incompatible type added.")

        self._add += instances


@dataclass
class OutputDelegate:

    _output: Output = field(default_factory=Output)

    def output(
        self,
        as_list: Optional[bool] = None,
        as_json: Optional[bool] = None,
        load_json: Optional[bool] = None,
        nested: Optional[bool] = None,
    ):
        """
        :param as_list:
            If each row only returns a single value, compile all of the results
            into a single list.
        :param as_json:
            The results are serialised into JSON. It's equivalent to running
            `json.dumps` on the result.
        :param load_json:
            If True, any JSON fields will have the JSON values returned from
            the database loaded as Python objects.
        """
        if as_list is not None:
            self._output.as_list = bool(as_list)

        if as_json is not None:
            self._output.as_json = bool(as_json)

        if load_json is not None:
            self._output.load_json = bool(load_json)

        if nested is not None:
            self._output.nested = bool(nested)

    def copy(self) -> OutputDelegate:
        return self.__class__(_output=self._output.copy())


@dataclass
class CallbackDelegate:

    _callbacks: dict[CallbackType, list[Callback]] = field(
        default_factory=lambda: {kind: [] for kind in CallbackType}
    )

    def callback(
        self,
        callbacks: Union[Callable, list[Callable]],
        *,
        on: CallbackType,
    ):
        pass

    async def invoke(self, results: Any, *, kind: CallbackType) -> Any:
        """
        Utility function that invokes the registered callbacks in the correct
        way, handling both sync and async callbacks. Only callbacks of the
        given kind are invoked.
        Results are passed through the callbacks in the order they were added,
        with each callback able to transform them. This function returns the
        transformed results.
        """
        for callback in self._callbacks[kind]:
            if asyncio.iscoroutinefunction(callback.target):
                results = await callback.target(results)
            else:
                results = callback.target(results)

        return results


@dataclass
class PrefetchDelegate:

    fk_columns: list[ForeignKey] = field(default_factory=list)

    def prefetch(self, *fk_columns: Union[ForeignKey, list[ForeignKey]]):
        pass


@dataclass
class ColumnsDelegate:

    selected_columns: Sequence[Selectable] = field(default_factory=list)

    def columns(self, *columns: Union[Selectable, list[Selectable]]):
        """
        :param columns:
            We accept ``Selectable`` and ``List[Selectable]`` here, in case
            someone passes in a list by accident when using ``all_columns()``,
            in which case we flatten the list.

        """
        _columns = flatten(columns)
        combined = list(self.selected_columns) + _columns
        self.selected_columns = combined

    def remove_secret_columns(self):
        pass


@dataclass
class ValuesDelegate:

    table: type[Table]
    _values: dict[Column, Any] = field(default_factory=dict)

    def values(self, values: dict[Union[Column, str], Any]):
        """
        Example usage:

        .. code-block:: python

            .values({MyTable.column_a: 1})

            # Or:
            .values({'column_a': 1})

            # Or:
            .values(column_a=1})

        """
        cleaned_values: dict[Column, Any] = {}
        for key, value in values.items():
            if isinstance(key, Column):
                column = key
            elif isinstance(key, str):
                column = self.table._meta.get_column_by_name(key)
            else:
                raise ValueError(
                    f"Unrecognised key - {key} is neither a Column or the "
                    "name of a Column."
                )
            cleaned_values[column] = value

        self._values.update(cleaned_values)

    def get_sql_values(self) -> list[Any]:
        pass


@dataclass
class OffsetDelegate:

    _offset: Optional[Offset] = None

    def offset(self, number: int = 0):
        self._offset = Offset(number)


@dataclass
class GroupBy:
    __slots__ = ("columns",)

    columns: Sequence[Union[Column, QueryString]]

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class GroupByDelegate:

    _group_by: Optional[GroupBy] = None

    def group_by(self, *columns: Union[Column, QueryString]):
        pass


class OnConflictAction(str, Enum):

    do_nothing = "DO NOTHING"
    do_update = "DO UPDATE"


@dataclass
class OnConflictItem:
    target: Optional[Union[str, Column, tuple[Column, ...]]] = None
    action: Optional[OnConflictAction] = None
    values: Optional[Sequence[Union[Column, tuple[Column, Any]]]] = None
    where: Optional[Combinable] = None

    @property
    def target_string(self) -> str:
        pass

    @property
    def action_string(self) -> QueryString:
        pass

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OnConflict:

    on_conflict_items: list[OnConflictItem] = field(default_factory=list)

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OnConflictDelegate:

    _on_conflict: OnConflict = field(default_factory=OnConflict)

    def on_conflict(
        self,
        target: Optional[Union[str, Column, tuple[Column, ...]]] = None,
        action: Union[
            OnConflictAction, Literal["DO NOTHING", "DO UPDATE"]
        ] = OnConflictAction.do_nothing,
        values: Optional[Sequence[Union[Column, tuple[Column, Any]]]] = None,
        where: Optional[Combinable] = None,
    ):
        action_: OnConflictAction
        if isinstance(action, OnConflictAction):
            action_ = action
        elif isinstance(action, str):
            action_ = OnConflictAction(action.upper())
        else:
            raise ValueError("Unrecognised `on conflict` action.")

        if target is None and action_ == OnConflictAction.do_update:
            raise ValueError(
                "The `target` option must be provided with DO UPDATE."
            )

        if where and action_ == OnConflictAction.do_nothing:
            raise ValueError(
                "The `where` option can only be used with DO NOTHING."
            )

        self._on_conflict.on_conflict_items.append(
            OnConflictItem(
                target=target, action=action_, values=values, where=where
            )
        )


class LockStrength(str, Enum):

    update = "UPDATE"
    no_key_update = "NO KEY UPDATE"
    share = "SHARE"
    key_share = "KEY SHARE"


@dataclass
class LockRows:
    __slots__ = ("lock_strength", "nowait", "skip_locked", "of")

    lock_strength: LockStrength
    nowait: bool
    skip_locked: bool
    of: tuple[type[Table], ...]

    def __post_init__(self):
        if not isinstance(self.lock_strength, LockStrength):
            raise TypeError("lock_strength must be a LockStrength")
        if not isinstance(self.nowait, bool):
            raise TypeError("nowait must be a bool")
        if not isinstance(self.skip_locked, bool):
            raise TypeError("skip_locked must be a bool")
        if not isinstance(self.of, tuple) or not all(
            hasattr(x, "_meta") for x in self.of
        ):
            raise TypeError("of must be a tuple of Table")
        if self.nowait and self.skip_locked:
            raise TypeError(
                "The nowait option cannot be used with skip_locked"
            )

    @property
    def querystring(self) -> QueryString:
        pass

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class LockRowsDelegate:

    _lock_rows: Optional[LockRows] = None

    def lock_rows(
        self,
        lock_strength: Union[
            LockStrength,
            Literal[
                "UPDATE",
                "NO KEY UPDATE",
                "KEY SHARE",
                "SHARE",
            ],
        ] = LockStrength.update,
        nowait=False,
        skip_locked=False,
        of: tuple[type[Table], ...] = (),
    ):
        pass
