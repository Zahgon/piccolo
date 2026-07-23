from __future__ import annotations

from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AddDelegate,
    OnConflictAction,
    OnConflictDelegate,
    ReturningDelegate,
)
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column
    from piccolo.table import Table


class Insert(
    Generic[TableInstance], Query[TableInstance, list[dict[str, Any]]]
):
    __slots__ = ("add_delegate", "on_conflict_delegate", "returning_delegate")

    def __init__(
        self, table: type[TableInstance], *instances: TableInstance, **kwargs
    ):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.returning_delegate = ReturningDelegate()
        self.on_conflict_delegate = OnConflictDelegate()
        self.add(*instances)


    def add(self: Self, *instances: Table) -> Self:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def returning(self: Self, *columns: Column) -> Self:
        self.returning_delegate.returning(columns)
        return self

    def on_conflict(
        self: Self,
        target: Optional[Union[str, Column, tuple[Column, ...]]] = None,
        action: Union[
            OnConflictAction, Literal["DO NOTHING", "DO UPDATE"]
        ] = OnConflictAction.do_nothing,
        values: Optional[Sequence[Union[Column, tuple[Column, Any]]]] = None,
        where: Optional[Combinable] = None,
    ) -> Self:
        if (
            self.engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() < 3.24
        ):
            raise NotImplementedError(
                "SQLite versions lower than 3.24 don't support ON CONFLICT"
            )

        if (
            self.engine_type in ("postgres", "cockroach")
            and len(self.on_conflict_delegate._on_conflict.on_conflict_items)
            == 1
        ):
            raise NotImplementedError(
                "Postgres and Cockroach only support a single ON CONFLICT "
                "clause."
            )

        self.on_conflict_delegate.on_conflict(
            target=target,
            action=action,
            values=values,
            where=where,
        )
        return self


    def _raw_response_callback(self, results: list):
        """
        Assign the ids of the created rows to the model instances.
        """
        for index, row in enumerate(results):
            table_instance: Table = self.add_delegate._add[index]
            setattr(
                table_instance,
                self.table._meta.primary_key._meta.name,
                row.get(
                    self.table._meta.primary_key._meta.db_column_name, None
                ),
            )
            table_instance._exists_in_db = True

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        pass


Self = TypeVar("Self", bound=Insert)
