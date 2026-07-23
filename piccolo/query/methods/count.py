from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, TypeVar, Union

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.functions.aggregate import Count as CountFunction
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


class Count(Query):

    __slots__ = ("where_delegate", "column", "_distinct")

    def __init__(
        self,
        table: type[Table],
        column: Optional[Column] = None,
        distinct: Optional[Sequence[Column]] = None,
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.column = column
        self._distinct = distinct
        self.where_delegate = WhereDelegate()


    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    def distinct(self: Self, columns: Optional[Sequence[Column]]) -> Self:
        pass


    async def response_handler(self, response) -> bool:
        return response[0]["count"]

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        pass


Self = TypeVar("Self", bound=Count)
