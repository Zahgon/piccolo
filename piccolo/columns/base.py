from __future__ import annotations

import copy
import datetime
import decimal
import inspect
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

from piccolo.columns.choices import Choice
from piccolo.columns.combination import Where
from piccolo.columns.defaults.base import Default
from piccolo.columns.defaults.interval import IntervalCustom
from piccolo.columns.indexes import IndexMethod
from piccolo.columns.operators.comparison import (
    ComparisonOperator,
    Equal,
    GreaterEqualThan,
    GreaterThan,
    ILike,
    In,
    IsNotNull,
    IsNull,
    LessEqualThan,
    LessThan,
    Like,
    NotEqual,
    NotIn,
    NotLike,
)
from piccolo.columns.reference import LazyTableReference
from piccolo.querystring import QueryString, Selectable
from piccolo.utils.warnings import colored_warning

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.column_types import ForeignKey
    from piccolo.query.functions.conditional import Coalesce
    from piccolo.query.methods.select import Select
    from piccolo.table import Table


class OnDelete(str, Enum):

    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __repr__(self):
        return self.__str__()


class OnUpdate(str, Enum):

    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __repr__(self):
        return self.__str__()


ReferencedTable = TypeVar("ReferencedTable", bound="Table")


@dataclass
class ForeignKeyMeta(Generic[ReferencedTable]):
    references: Union[type[ReferencedTable], LazyTableReference]
    on_delete: OnDelete
    on_update: OnUpdate
    target_column: Union[Column, str, None]
    proxy_columns: list[Column] = field(default_factory=list)

    @property
    def resolved_references(self) -> type[Table]:
        pass

    @property
    def resolved_target_column(self) -> Column:
        pass

    def copy(self) -> ForeignKeyMeta[ReferencedTable]:
        kwargs = self.__dict__.copy()
        kwargs.update(proxy_columns=self.proxy_columns.copy())
        return self.__class__(**kwargs)

    def __copy__(self) -> ForeignKeyMeta[ReferencedTable]:
        return self.copy()

    def __deepcopy__(self, memo) -> ForeignKeyMeta[ReferencedTable]:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()


@dataclass
class ColumnMeta:

    null: bool = False
    primary_key: bool = False
    unique: bool = False
    index: bool = False
    index_method: IndexMethod = IndexMethod.btree
    required: bool = False
    help_text: Optional[str] = None
    choices: Optional[type[Enum]] = None
    secret: bool = False
    auto_update: Any = ...

    params: dict[str, Any] = field(default_factory=dict)


    _db_column_name: Optional[str] = None

    @property
    def db_column_name(self) -> str:
        pass

    @db_column_name.setter
    def db_column_name(self, value: str):
        pass


    _name: Optional[str] = None
    _table: Optional[type[Table]] = None

    @property
    def name(self) -> str:
        pass

    @name.setter
    def name(self, value: str):
        pass

    @property
    def table(self) -> type[Table]:
        if not self._table:
            raise ValueError(
                "`_table` isn't defined - the Table Metaclass should set it."
            )
        return self._table

    @table.setter
    def table(self, value: type[Table]):
        self._table = value


    call_chain: list["ForeignKey"] = field(default_factory=list)


    @property
    def engine_type(self) -> str:
        pass

    def get_choices_dict(self) -> Optional[dict[str, Any]]:
        """
        Return the choices Enum as a dict. It maps the attribute name to a
        dict containing the display name, and value.
        """
        if self.choices is None:
            return None
        output = {}
        for element in self.choices:
            if isinstance(element.value, Choice):
                display_name = element.value.display_name
                value = element.value.value
            else:
                display_name = element.name.replace("_", " ").title()
                value = element.value

            output[element.name] = {
                "display_name": display_name,
                "value": value,
            }

        return output


    def get_default_alias(self):
        column_name = self.db_column_name

        if self.call_chain:
            column_name = (
                ".".join(
                    cast(str, i._meta.db_column_name) for i in self.call_chain
                )
                + f".{column_name}"
            )

        return column_name

    def _get_path(self, include_quotes: bool = False):
        pass

    def get_full_name(
        self,
        with_alias: bool = True,
        include_quotes: bool = True,
    ) -> str:
        pass


    def copy(self) -> ColumnMeta:
        kwargs = self.__dict__.copy()
        kwargs.update(
            params=self.params.copy(),
            call_chain=self.call_chain.copy(),
        )

        field_names = [i.name for i in fields(self.__class__)]
        kwargs = {
            kwarg: value
            for kwarg, value in kwargs.items()
            if kwarg in field_names
        }

        return self.__class__(**kwargs)

    def __copy__(self) -> ColumnMeta:
        return self.copy()

    def __deepcopy__(self, memo) -> ColumnMeta:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()


class ColumnKwargs(TypedDict, total=False):

    null: bool
    primary_key: bool
    unique: bool
    index: bool
    index_method: IndexMethod
    required: bool
    help_text: Optional[str]
    choices: Optional[type[Enum]]
    db_column_name: Optional[str]
    secret: bool
    auto_update: Any


class Column(Selectable):

    value_type: type = int
    default: Any

    def __init__(
        self,
        null: bool = False,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        index_method: IndexMethod = IndexMethod.btree,
        required: bool = False,
        help_text: Optional[str] = None,
        choices: Optional[type[Enum]] = None,
        db_column_name: Optional[str] = None,
        secret: bool = False,
        auto_update: Any = ...,
        **kwargs,
    ) -> None:
        if kwargs.get("primary") is True:
            primary_key = True

        kwargs.update(
            {
                "null": null,
                "primary_key": primary_key,
                "unique": unique,
                "index": index,
                "index_method": index_method,
                "choices": choices,
                "db_column_name": db_column_name,
                "secret": secret,
            }
        )

        if choices is not None:
            self._validate_choices(choices, allowed_type=self.value_type)

        self._meta = ColumnMeta(
            null=null,
            primary_key=primary_key,
            unique=unique,
            index=index,
            index_method=index_method,
            params=kwargs,
            required=required,
            help_text=help_text,
            choices=choices,
            _db_column_name=db_column_name,
            secret=secret,
            auto_update=auto_update,
        )

        self._alias: Optional[str] = None

    def _validate_default(
        self,
        default: Any,
        allowed_types: Iterable[Union[None, type[Any]]],
        allow_recursion: bool = True,
    ) -> bool:
        pass

    def _validate_choices(
        self, choices: type[Enum], allowed_type: type[Any]
    ) -> bool:
        pass

    def is_in(self, values: Union[Select, QueryString, list[Any]]) -> Where:
        from piccolo.query.methods.select import Select

        if isinstance(values, list):
            if len(values) == 0:
                raise ValueError(
                    "The `values` list argument must contain at least one "
                    "value."
                )
        elif isinstance(values, Select):
            if len(values.columns_delegate.selected_columns) != 1:
                raise ValueError(
                    "A sub select must only return a single column."
                )
            values = values.querystrings[0]

        return Where(column=self, values=values, operator=In)

    def not_in(self, values: Union[Select, QueryString, list[Any]]) -> Where:
        from piccolo.query.methods.select import Select

        if isinstance(values, list):
            if len(values) == 0:
                raise ValueError(
                    "The `values` list argument must contain at least one "
                    "value."
                )
        elif isinstance(values, Select):
            if len(values.columns_delegate.selected_columns) != 1:
                raise ValueError(
                    "A sub select must only return a single column."
                )
            values = values.querystrings[0]

        return Where(column=self, values=values, operator=NotIn)

    def like(self, value: str) -> Where:
        pass

    def ilike(self, value: str) -> Where:
        pass

    def not_like(self, value: str) -> Where:
        pass

    def __or__(self, value) -> Coalesce:
        from piccolo.query.functions.conditional import Coalesce

        return Coalesce(self, value)

    def __lt__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessThan)

    def __le__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterEqualThan)

    def _equals(self, column: Column, including_joins: bool = False) -> bool:
        """
        We override ``__eq__``, in order to do queries such as:

        .. code-block:: python

            await Band.select().where(Band.name == 'Pythonistas')

        But this means that comparisons such as this can give unexpected
        results:

        .. code-block:: python

            # We would expect the answer to be `True`, but we get `Where`
            # instead:
            >>> MyTable.some_column == MyTable.some_column
            <Where>

        Also, column comparison is sometimes more complex than it appears. This
        is why we have this custom method for comparing columns.

        Take this example:

        .. code-block:: python

            Band.manager.name == Manager.name

        They both refer to the ``name`` column on the ``Manager`` table, except
        one has joins and the other doesn't.

        :param including_joins:
            If ``True``, then we check if the columns are the same, as well as
            their joins, i.e. ``Band.manager.name`` != ``Manager.name``.

        """
        if isinstance(column, Column):
            if (
                self._meta.name == column._meta.name
                and self._meta.table._meta.tablename
                == column._meta.table._meta.tablename
            ):
                if including_joins:
                    if len(column._meta.call_chain) == len(
                        self._meta.call_chain
                    ):
                        return all(
                            column_a._equals(column_b, including_joins=False)
                            for column_a, column_b in zip(
                                column._meta.call_chain,
                                self._meta.call_chain,
                            )
                        )

                else:
                    return True

        return False

    def __eq__(self, value) -> Where:  # type: ignore[override]
        if value is None:
            return Where(column=self, operator=IsNull)
        else:
            return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:  # type: ignore[override]
        if value is None:
            return Where(column=self, operator=IsNotNull)
        else:
            return Where(column=self, value=value, operator=NotEqual)

    def __hash__(self):
        return hash(self._meta.name)

    def is_null(self) -> Where:
        pass

    def is_not_null(self) -> Where:
        pass

    def as_alias(self, name: str) -> Column:
        """
        Allows column names to be changed in the result of a select.

        For example:

        .. code-block:: python

            >>> await Band.select(Band.name.as_alias('title')).run()
            {'title': 'Pythonistas'}

        """
        column = copy.deepcopy(self)
        column._alias = name
        return column

    def join_on(self, column: Column) -> ForeignKey:
        """
        Joins are typically performed via foreign key columns. For example,
        here we get the band's name and the manager's name::

            class Manager(Table):
                name = Varchar()

            class Band(Table):
                name = Varchar()
                manager = ForeignKey(Manager)

            >>> await Band.select(Band.name, Band.manager.name)

        The ``join_on`` method lets you join tables even when foreign keys
        don't exist, by joining on a column in another table.

        For example, here we want to get the manager's email, but no foreign
        key exists::

            class Manager(Table):
                name = Varchar(unique=True)
                email = Varchar()

            class Band(Table):
                name = Varchar()
                manager_name = Varchar()

            >>> await Band.select(
            ...     Band.name,
            ...     Band.manager_name.join_on(Manager.name).email
            ... )

        """
        from piccolo.columns.column_types import ForeignKey

        virtual_foreign_key = ForeignKey(
            references=column._meta.table, target_column=column
        )
        virtual_foreign_key._meta._name = self._meta.name
        virtual_foreign_key._meta.call_chain = [*self._meta.call_chain]
        virtual_foreign_key._meta._table = self._meta.table
        virtual_foreign_key.set_proxy_columns()
        return virtual_foreign_key

    def get_default_value(self) -> Any:
        """
        If the column has a default attribute, return it. If it's callable,
        return the response instead.
        """
        default = getattr(self, "default", ...)
        if default is not ...:
            default = default.value if isinstance(default, Enum) else default
            is_callable = hasattr(default, "__call__")
            return default() if is_callable else default  # type: ignore
        return None

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> QueryString:
        pass

    def get_where_string(self, engine_type: str) -> QueryString:
        pass

    def get_sql_value(
        self,
        value: Any,
        delimiter: str = "'",
    ) -> str:
        pass

    @property
    def column_type(self):
        return self.__class__.__name__.upper()

    @property
    def table_alias(self) -> str:
        pass

    @property
    def ddl(self) -> str:
        pass

    def copy(self: Self) -> Self:
        column = copy.copy(self)
        column._meta = self._meta.copy()
        return column

    def __deepcopy__(self, memo) -> Column:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()

    def __str__(self):
        return self.ddl.__str__()

    def __repr__(self):
        try:
            table = self._meta.table
        except ValueError:
            table_class_name = "Unknown"
        else:
            table_class_name = table.__name__
        return (
            f"{table_class_name}.{self._meta.name} - "
            f"{self.__class__.__name__}"
        )


Self = TypeVar("Self", bound=Column)
