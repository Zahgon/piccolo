from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json

if TYPE_CHECKING:
    from piccolo.columns.column_types import JSON


class JSONQueryString(QueryString):

    def clean_value(self, value: Any):
        pass

    def __eq__(self, value) -> QueryString:  # type: ignore[override]
        value = self.clean_value(value)
        return QueryString("{} = {}", self, value)

    def __ne__(self, value) -> QueryString:  # type: ignore[override]
        value = self.clean_value(value)
        return QueryString("{} != {}", self, value)

    def eq(self, value) -> QueryString:
        pass

    def ne(self, value) -> QueryString:
        pass


class GetChildElement(JSONQueryString):

    def __init__(
        self,
        identifier: Union[JSON, QueryString],
        key: Union[str, int, QueryString],
        alias: Optional[str] = None,
    ):
        if isinstance(key, int):
            key = QueryString("{}::int", key)

        super().__init__("{} -> {}", identifier, key, alias=alias)

    def arrow(self, key: Union[str, int, QueryString]) -> GetChildElement:
        pass

    def __getitem__(
        self, value: Union[str, int, QueryString]
    ) -> GetChildElement:
        return GetChildElement(identifier=self, key=value, alias=self._alias)


class GetElementFromPath(JSONQueryString):

    def __init__(
        self,
        identifier: Union[JSON, QueryString],
        path: list[Union[str, int]],
        alias: Optional[str] = None,
    ):
        """
        :param path:
            For example: ``["technician", 0, "name"]``.

        """
        super().__init__(
            "{} #> {}",
            identifier,
            [str(i) if isinstance(i, int) else i for i in path],
            alias=alias,
        )
