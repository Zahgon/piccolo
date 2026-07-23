from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Union

from piccolo.columns.base import Column
from piccolo.query.base import Query
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class DropIndex(Query):
    def __init__(
        self,
        table: type[Table],
        columns: Union[list[Column], list[str]],
        if_exists: bool = True,
        **kwargs,
    ):
        self.columns = columns
        self.if_exists = if_exists
        super().__init__(table, **kwargs)

    @property
    def column_names(self) -> list[str]:
        pass

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        pass
