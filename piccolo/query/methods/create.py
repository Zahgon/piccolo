from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from piccolo.query.base import DDL
from piccolo.query.methods.create_index import CreateIndex

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Create(DDL):

    __slots__ = ("if_not_exists", "only_default_columns", "auto_create_schema")

    def __init__(
        self,
        table: type[Table],
        if_not_exists: bool = False,
        only_default_columns: bool = False,
        auto_create_schema: bool = True,
        **kwargs,
    ):
        """
        :param table:
            The table to create.
        :param if_not_exists:
            If ``True``, no error will be raised if this table already exists.
        :param only_default_columns:
            If ``True``, just the basic table and default primary key are
            created, rather than all columns. Not typically needed.
        :param auto_create_schema:
            If the table belongs to a database schema, then make sure the
            schema exists before creating the table.

        """
        super().__init__(table, **kwargs)
        self.if_not_exists = if_not_exists
        self.only_default_columns = only_default_columns
        self.auto_create_schema = auto_create_schema

    @property
    def default_ddl(self) -> Sequence[str]:
        pass
