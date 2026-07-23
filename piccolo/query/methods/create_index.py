from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Union

from piccolo.columns import Column
from piccolo.columns.indexes import IndexMethod
from piccolo.query.base import DDL

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class CreateIndex(DDL):
    def __init__(
        self,
        table: type[Table],
        columns: Union[list[Column], list[str]],
        method: IndexMethod = IndexMethod.btree,
        if_not_exists: bool = False,
        **kwargs,
    ):
        self.columns = columns
        self.method = method
        self.if_not_exists = if_not_exists
        super().__init__(table, **kwargs)

    @property
    def column_names(self) -> list[str]:
        pass

    @property
    def prefix(self) -> str:
        pass

    @property
    def postgres_ddl(self) -> Sequence[str]:
        pass

    @property
    def cockroach_ddl(self) -> Sequence[str]:
        pass

    @property
    def sqlite_ddl(self) -> Sequence[str]:
        pass
