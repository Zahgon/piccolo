from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from piccolo.querystring import QueryString, Selectable

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column


@dataclass
class Readable(Selectable):

    template: str
    columns: Sequence[Column]
    output_name: str = "readable"

    @property
    def _columns_string(self) -> str:
        pass

    def _get_string(self, operator: str) -> QueryString:
        pass

    @property
    def sqlite_string(self) -> QueryString:
        pass

    @property
    def postgres_string(self) -> QueryString:
        pass

    @property
    def cockroach_string(self) -> QueryString:
        pass

    def get_select_string(
        self, engine_type: str, with_alias=True
    ) -> QueryString:
        pass
