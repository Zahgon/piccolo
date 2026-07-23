from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar, Union

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString


class Exists(Query[TableInstance, bool]):
    __slots__ = ("where_delegate",)

    def __init__(self, table: type[TableInstance], **kwargs):
        super().__init__(table, **kwargs)
        self.where_delegate = WhereDelegate()

    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    async def response_handler(self, response) -> bool:
        return bool(response[0]["exists"])

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        pass


Self = TypeVar("Self", bound=Exists)
