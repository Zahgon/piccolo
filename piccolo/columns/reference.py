
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.column_types import ForeignKey
    from piccolo.table import Table


@dataclass
class LazyTableReference:

    table_class_name: str
    app_name: Optional[str] = None
    module_path: Optional[str] = None

    def __post_init__(self):
        if self.app_name is None and self.module_path is None:
            raise ValueError(
                "You must specify either app_name or module_path."
            )
        if self.app_name and self.module_path:
            raise ValueError(
                "Specify either app_name or module_path - not both."
            )

    def resolve(self) -> type[Table]:
        if self.app_name is not None:
            from piccolo.conf.apps import Finder

            finder = Finder()
            return finder.get_table_with_name(
                app_name=self.app_name, table_class_name=self.table_class_name
            )

        if self.module_path:
            module = importlib.import_module(self.module_path)
            table: Optional[type[Table]] = getattr(
                module, self.table_class_name, None
            )

            from piccolo.table import Table

            if (
                table is not None
                and inspect.isclass(table)
                and issubclass(table, Table)
            ):
                return table
            else:
                raise ValueError(
                    "Can't find a Table subclass called "
                    f"{self.table_class_name} in {self.module_path}"
                )

        raise ValueError("You must specify either app_name or module_path.")

    def __str__(self):
        if self.app_name:
            return f"App {self.app_name}.{self.table_class_name}"
        elif self.module_path:
            return f"Module {self.module_path}.{self.table_class_name}"
        else:
            return "Unknown"


@dataclass
class LazyColumnReferenceStore:
    foreign_key_columns: list[ForeignKey] = field(default_factory=list)

    def for_table(self, table: type[Table]) -> list[ForeignKey]:
        pass

    def for_tablename(self, tablename: str) -> list[ForeignKey]:
        pass


LAZY_COLUMN_REFERENCES: LazyColumnReferenceStore = LazyColumnReferenceStore()
