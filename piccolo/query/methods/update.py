from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional, Union

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    ReturningDelegate,
    ValuesDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column


class UpdateError(Exception):
    pass


class Update(Query[TableInstance, list[Any]]):
    __slots__ = (
        "force",
        "returning_delegate",
        "values_delegate",
        "where_delegate",
    )

    def __init__(
        self, table: type[TableInstance], force: bool = False, **kwargs
    ):
        super().__init__(table, **kwargs)
        self.force = force
        self.returning_delegate = ReturningDelegate()
        self.values_delegate = ValuesDelegate(table=table)
        self.where_delegate = WhereDelegate()


    def values(
        self,
        values: Optional[dict[Union[Column, str], Any]] = None,
        **kwargs,
    ) -> Update:
        if values is None:
            values = {}
        values = dict(values, **kwargs)
        self.values_delegate.values(values)
        return self

    def where(self, *where: Union[Combinable, QueryString]) -> Update:
        self.where_delegate.where(*where)
        return self

    def returning(self, *columns: Column) -> Update:
        self.returning_delegate.returning(columns)
        return self


    def _validate(self):
        """
        Called at the start of :meth:`piccolo.query.base.Query.run` to make
        sure the user has configured the query correctly before running it.
        """
        if len(self.values_delegate._values) == 0:
            raise ValueError("No values were specified to update.")

        for column, _ in self.values_delegate._values.items():
            if len(column._meta.call_chain) > 0:
                raise ValueError(
                    "Related values can't be updated via an update."
                )

        if (not self.where_delegate._where) and (not self.force):
            classname = self.table.__name__
            raise UpdateError(
                "Do you really want to update all rows in "
                f"{classname}? If so, use pass `force=True` into "
                f"`{classname}.update`. Otherwise, add a where clause."
            )


    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        pass
