from __future__ import annotations

from collections.abc import Sequence

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Indexes(Query):

    @property
    def postgres_querystrings(self) -> Sequence[QueryString]:
        pass

    @property
    def cockroach_querystrings(self) -> Sequence[QueryString]:
        pass

    @property
    def sqlite_querystrings(self) -> Sequence[QueryString]:
        pass

    async def response_handler(self, response):
        return [i["name"] for i in response]
