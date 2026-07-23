from __future__ import annotations

import inspect
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Optional

from piccolo.apps.migrations.auto.diffable_table import (
    DiffableTable,
    TableDelta,
)
from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.auto.operations import (
    ChangeTableSchema,
    RenameColumn,
    RenameTable,
)
from piccolo.apps.migrations.auto.serialisation import (
    Definition,
    Import,
    UniqueGlobalNames,
    serialise_params,
)
from piccolo.utils.printing import get_fixed_length_string


@dataclass
class RenameTableCollection:
    rename_tables: list[RenameTable] = field(default_factory=list)

    def append(self, renamed_table: RenameTable):
        self.rename_tables.append(renamed_table)

    @property
    def old_class_names(self):
        pass

    @property
    def new_class_names(self):
        pass

    def was_renamed_from(self, old_class_name: str) -> bool:
        pass

    def renamed_from(self, new_class_name: str) -> Optional[str]:
        pass


@dataclass
class ChangeTableSchemaCollection:
    collection: list[ChangeTableSchema] = field(default_factory=list)

    def append(self, change_table_schema: ChangeTableSchema):
        self.collection.append(change_table_schema)


@dataclass
class RenameColumnCollection:
    rename_columns: list[RenameColumn] = field(default_factory=list)

    def append(self, rename_column: RenameColumn):
        self.rename_columns.append(rename_column)

    def for_table_class_name(
        self, table_class_name: str
    ) -> list[RenameColumn]:
        return [
            i
            for i in self.rename_columns
            if i.table_class_name == table_class_name
        ]

    @property
    def old_column_names(self):
        pass

    @property
    def new_column_names(self):
        pass


@dataclass
class AlterStatements:
    statements: list[str] = field(default_factory=list)
    extra_imports: list[Import] = field(default_factory=list)
    extra_definitions: list[Definition] = field(default_factory=list)

    def extend(self, alter_statements: AlterStatements):
        self.statements.extend(alter_statements.statements)
        self.extra_imports.extend(alter_statements.extra_imports)
        self.extra_definitions.extend(alter_statements.extra_definitions)
        return self


@dataclass
class SchemaDiffer:

    schema: list[DiffableTable]
    schema_snapshot: list[DiffableTable]

    auto_input: Optional[str] = None


    def __post_init__(self) -> None:
        self.schema_snapshot_map: dict[str, DiffableTable] = {
            i.class_name: i for i in self.schema_snapshot
        }
        self.table_schema_changes_collection = (
            self.check_table_schema_changes()
        )
        self.rename_tables_collection = self.check_rename_tables()
        self.rename_columns_collection = self.check_renamed_columns()

    def check_rename_tables(self) -> RenameTableCollection:
        pass

    def check_table_schema_changes(self) -> ChangeTableSchemaCollection:
        pass

    def check_renamed_columns(self) -> RenameColumnCollection:
        pass


    def _stringify_func(
        self,
        func: Callable,
        params: dict[str, Any],
        prefix: Optional[str] = None,
    ) -> AlterStatements:
        """
        Generates a string representing how to call the given function with the
        give params. For example::

            def my_callable(arg_1: str, arg_2: str):
                ...

            >>> _stringify_func(
            ...     my_callable,
            ...     {"arg_1": "a", "arg_2": "b"}
            ... ).statements
            ['my_callable(arg_1="a", arg_2="b")']

        """
        signature = inspect.signature(func)

        if "self" in signature.parameters.keys():
            params["self"] = None

        serialised_params = serialise_params(params)

        func_name = func.__name__

        bound = signature.bind(**serialised_params.params)
        bound.apply_defaults()

        args = bound.arguments
        if "self" in args:
            args.pop("self")

        args_str = ", ".join(f"{i}={repr(j)}" for i, j in args.items())

        return AlterStatements(
            statements=[f"{prefix or ''}{func_name}({args_str})"],
            extra_definitions=serialised_params.extra_definitions,
            extra_imports=serialised_params.extra_imports,
        )


    @property
    def create_tables(self) -> AlterStatements:
        new_tables: list[DiffableTable] = list(
            set(self.schema) - set(self.schema_snapshot)
        )

        new_tables = [
            i
            for i in new_tables
            if i.class_name
            not in self.rename_tables_collection.new_class_names
        ]

        alter_statements = AlterStatements()

        for i in new_tables:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.add_table,
                    params={
                        "class_name": i.class_name,
                        "tablename": i.tablename,
                        "schema": i.schema,
                    },
                    prefix="manager.",
                )
            )

        return alter_statements

    @property
    def drop_tables(self) -> AlterStatements:
        drop_tables: list[DiffableTable] = list(
            set(self.schema_snapshot) - set(self.schema)
        )

        drop_tables = [
            i
            for i in drop_tables
            if i.class_name
            not in self.rename_tables_collection.old_class_names
        ]

        alter_statements = AlterStatements()

        for i in drop_tables:
            alter_statements.extend(
                self._stringify_func(
                    func=MigrationManager.drop_table,
                    params={
                        "class_name": i.class_name,
                        "tablename": i.tablename,
                        "schema": i.schema,
                    },
                    prefix="manager.",
                )
            )

        return alter_statements

    @property
    def rename_tables(self) -> AlterStatements:
        pass

    @property
    def change_table_schemas(self) -> AlterStatements:
        pass


    def _get_snapshot_table(
        self, table_class_name: str
    ) -> Optional[DiffableTable]:
        pass

    @property
    def alter_columns(self) -> AlterStatements:
        pass

    @property
    def drop_columns(self) -> AlterStatements:
        pass

    @property
    def add_columns(self) -> AlterStatements:
        pass

    @property
    def rename_columns(self) -> AlterStatements:
        pass


    @property
    def new_table_columns(self) -> AlterStatements:
        pass


    def get_alter_statements(self) -> list[AlterStatements]:
        """
        Call to execute the necessary alter commands on the database.
        """
        alter_statements: dict[str, AlterStatements] = {
            "Created tables": self.create_tables,
            "Dropped tables": self.drop_tables,
            "Renamed tables": self.rename_tables,
            "Tables which changed schema": self.change_table_schemas,
            "Created table columns": self.new_table_columns,
            "Dropped columns": self.drop_columns,
            "Columns added to existing tables": self.add_columns,
            "Renamed columns": self.rename_columns,
            "Altered columns": self.alter_columns,
        }

        for message, statements in alter_statements.items():
            _message = get_fixed_length_string(message, length=40)
            count = len(statements.statements)
            print(f"{_message} {count}")

        return list(alter_statements.values())
