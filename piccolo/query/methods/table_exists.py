from __future__ import annotations

from collections.abc import Sequence

from piccolo.custom_types import TableInstance
from piccolo.query.base import Query
from piccolo.querystring import QueryString


class TableExists(Query[TableInstance, bool]):

    __slots__: tuple = ()

    async def response_handler(self, response):
        return bool(response[0]["exists"])

    @property
    def sqlite_querystrings(self) -> Sequence[QueryString]:
        pass

    @property
    def postgres_querystrings(self) -> Sequence[QueryString]:
        pass

    @property
    def cockroach_querystrings(self) -> Sequence[QueryString]:
        pass
