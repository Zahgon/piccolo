from __future__ import annotations

import abc
from typing import Optional, cast

from piccolo.engine.base import Engine
from piccolo.engine.finder import engine_finder
from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync


class SchemaDDLBase(abc.ABC):
    db: Engine

    @property
    @abc.abstractmethod
    def ddl(self) -> str:
        pass

    def __await__(self):
        return self.run().__await__()

    async def run(self, in_pool=True):
        return await self.db.run_ddl(self.ddl, in_pool=in_pool)

    def run_sync(self, *args, **kwargs):
        return run_sync(self.run(*args, **kwargs))

    def __str__(self) -> str:
        return self.ddl.__str__()


class CreateSchema(SchemaDDLBase):
    def __init__(
        self,
        schema_name: str,
        *,
        if_not_exists: bool,
        db: Engine,
    ):
        self.schema_name = schema_name
        self.if_not_exists = if_not_exists
        self.db = db

    async def run(self, *args, **kwargs):
        if self.schema_name == "public" or self.schema_name is None:
            return

        return await super().run(self, *args, **kwargs)

    @property
    def ddl(self) -> str:
        pass


class DropSchema(SchemaDDLBase):
    def __init__(
        self,
        schema_name: str,
        *,
        if_exists: bool,
        cascade: bool,
        db: Engine,
    ):
        self.schema_name = schema_name
        self.if_exists = if_exists
        self.cascade = cascade
        self.db = db

    @property
    def ddl(self) -> str:
        pass


class RenameSchema(SchemaDDLBase):
    def __init__(
        self,
        schema_name: str,
        new_schema_name: str,
        db: Engine,
    ):
        self.schema_name = schema_name
        self.new_schema_name = new_schema_name
        self.db = db

    @property
    def ddl(self):
        pass


class MoveTable(SchemaDDLBase):
    def __init__(
        self,
        table_name: str,
        new_schema: str,
        db: Engine,
        current_schema: Optional[str] = None,
    ):
        self.table_name = table_name
        self.current_schema = current_schema
        self.new_schema = new_schema
        self.db = db

    @property
    def ddl(self):
        pass


class ListTables:
    def __init__(self, db: Engine, schema_name: str):
        self.db = db
        self.schema_name = schema_name

    async def run(self) -> list[str]:
        response = cast(
            list[dict],
            await self.db.run_querystring(
                QueryString(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = {}
                """,
                    self.schema_name,
                )
            ),
        )
        return [i["table_name"] for i in response]

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class ListSchemas:
    def __init__(self, db: Engine):
        self.db = db

    async def run(self) -> list[str]:
        response = cast(
            list[dict],
            await self.db.run_querystring(
                QueryString(
                    "SELECT schema_name FROM information_schema.schemata"
                )
            ),
        )
        return [i["schema_name"] for i in response]

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class SchemaManager:
    def __init__(self, db: Optional[Engine] = None):
        """
        A useful utility class for interacting with schemas.

        :param db:
            Used to execute the database queries. If not specified, we try and
            import it from ``piccolo_conf.py``.
        """
        db = db or engine_finder()

        if db is None:
            raise ValueError("The DB can't be found.")

        self.db = db

    def create_schema(
        self, schema_name: str, *, if_not_exists: bool = True
    ) -> CreateSchema:
        """
        Creates the specified schema::

            >>> await SchemaManager().create_schema(schema_name="music")

        :param schema_name:
            The name of the schema to create.
        :param if_not_exists:
            No error will be raised if the schema already exists.

        """
        return CreateSchema(
            schema_name=schema_name,
            if_not_exists=if_not_exists,
            db=self.db,
        )

    def drop_schema(
        self,
        schema_name: str,
        *,
        if_exists: bool = True,
        cascade: bool = False,
    ) -> DropSchema:
        pass

    def rename_schema(
        self, schema_name: str, new_schema_name: str
    ) -> RenameSchema:
        pass

    def move_table(
        self,
        table_name: str,
        new_schema: str,
        current_schema: Optional[str] = None,
    ) -> MoveTable:
        """
        Moves a table to a different schema::

            >>> await SchemaManager().move_schema(
            ...     table_name='my_table',
            ...     new_schema='schema_1'
            ... )

        :param table_name:
            The name of the table to move.
        :param new_schema:
            The name of the scheam you want to move the table too.
        :current_schema:
            If not specified, ``'public'`` is assumed.

        """
        return MoveTable(
            table_name=table_name,
            new_schema=new_schema,
            current_schema=current_schema,
            db=self.db,
        )

    def list_tables(self, schema_name: str) -> ListTables:
        pass

    def list_schemas(self) -> ListSchemas:
        pass
