from __future__ import annotations

import contextvars
import datetime
import enum
import os
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from functools import partial, wraps
from typing import TYPE_CHECKING, Any, Optional, Union

from typing_extensions import Self

from piccolo.engine.base import (
    BaseAtomic,
    BaseBatch,
    BaseTransaction,
    Engine,
    validate_savepoint_name,
)
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import DDL, Query
from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json, load_json
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.sync import run_sync

aiosqlite = LazyLoader("aiosqlite", globals(), "aiosqlite")


if TYPE_CHECKING:  # pragma: no cover
    from aiosqlite import Connection, Cursor  # type: ignore

    from piccolo.table import Table






def convert_numeric_in(value: Decimal) -> float:
    pass


def convert_uuid_in(value: uuid.UUID) -> str:
    pass


def convert_time_in(value: datetime.time) -> str:
    pass


def convert_date_in(value: datetime.date) -> str:
    pass


def convert_datetime_in(value: datetime.datetime) -> str:
    pass


def convert_timedelta_in(value: datetime.timedelta) -> float:
    pass


def convert_array_in(value: list) -> str:
    pass




ADAPTERS: dict[type, Callable[[Any], Any]] = {
    Decimal: convert_numeric_in,
    uuid.UUID: convert_uuid_in,
    datetime.time: convert_time_in,
    datetime.date: convert_date_in,
    datetime.datetime: convert_datetime_in,
    datetime.timedelta: convert_timedelta_in,
    list: convert_array_in,
}

for value_type, adapter in ADAPTERS.items():
    sqlite3.register_adapter(value_type, adapter)




def decode_to_string(converter: Callable[[str], Any]):
    pass


@decode_to_string
def convert_numeric_out(value: str) -> Decimal:
    pass


@decode_to_string
def convert_int_out(value: str) -> int:
    pass


@decode_to_string
def convert_uuid_out(value: str) -> uuid.UUID:
    pass


@decode_to_string
def convert_date_out(value: str) -> datetime.date:
    pass


@decode_to_string
def convert_time_out(value: str) -> datetime.time:
    pass


@decode_to_string
def convert_seconds_out(value: str) -> datetime.timedelta:
    pass


@decode_to_string
def convert_boolean_out(value: str) -> bool:
    pass


@decode_to_string
def convert_timestamp_out(value: str) -> datetime.datetime:
    pass


@decode_to_string
def convert_timestamptz_out(value: str) -> datetime.datetime:
    pass


@decode_to_string
def convert_array_out(value: str) -> list:
    pass


def convert_complex_array_out(value: bytes, converter: Callable):
    pass


@decode_to_string
def convert_M2M_out(value: str) -> list:
    pass



CONVERTERS = {
    "NUMERIC": convert_numeric_out,
    "INTEGER": convert_int_out,
    "UUID": convert_uuid_out,
    "DATE": convert_date_out,
    "TIME": convert_time_out,
    "SECONDS": convert_seconds_out,
    "BOOLEAN": convert_boolean_out,
    "TIMESTAMP": convert_timestamp_out,
    "TIMESTAMPTZ": convert_timestamptz_out,
    "M2M": convert_M2M_out,
}

for column_name, converter in CONVERTERS.items():
    sqlite3.register_converter(column_name, converter)


sqlite3.register_converter("ARRAY", convert_array_out)

for column_name in ("TIMESTAMP", "TIMESTAMPTZ", "DATE", "TIME", "NUMERIC"):
    sqlite3.register_converter(
        f"ARRAY_{column_name}",
        partial(
            convert_complex_array_out,
            converter=CONVERTERS[column_name],
        ),
    )



@dataclass
class AsyncBatch(BaseBatch):
    connection: Connection
    query: Query
    batch_size: int

    _cursor: Optional[Cursor] = None

    @property
    def cursor(self) -> Cursor:
        pass

    async def next(self) -> list[dict]:
        data = await self.cursor.fetchmany(self.batch_size)
        return await self.query._process_results(data)

    def __aiter__(self: Self) -> Self:
        return self

    async def __anext__(self) -> list[dict]:
        response = await self.next()
        if response == []:
            raise StopAsyncIteration()
        return response

    async def __aenter__(self: Self) -> Self:
        querystring = self.query.querystrings[0]
        template, template_args = querystring.compile_string()

        self._cursor = await self.connection.execute(template, *template_args)
        return self

    async def __aexit__(self, exception_type, exception, traceback):
        await self.cursor.close()
        await self.connection.close()
        return exception is not None




class TransactionType(enum.Enum):

    deferred = "DEFERRED"
    immediate = "IMMEDIATE"
    exclusive = "EXCLUSIVE"


class Atomic(BaseAtomic):

    __slots__ = ("engine", "queries", "transaction_type")

    def __init__(
        self,
        engine: SQLiteEngine,
        transaction_type: TransactionType = TransactionType.deferred,
    ):
        self.engine = engine
        self.transaction_type = transaction_type
        self.queries: list[Union[Query, DDL]] = []

    def add(self, *query: Union[Query, DDL]):
        self.queries += list(query)

    async def run(self):
        from piccolo.query.methods.objects import Create, GetOrCreate

        try:
            async with self.engine.transaction(
                transaction_type=self.transaction_type
            ):
                for query in self.queries:
                    if isinstance(query, (Query, DDL, Create, GetOrCreate)):
                        await query.run()
                    else:
                        raise ValueError("Unrecognised query")
            self.queries = []
        except Exception as exception:
            self.queries = []
            raise exception from exception

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()




class Savepoint:
    def __init__(self, name: str, transaction: SQLiteTransaction):
        self.name = name
        self.transaction = transaction

    async def rollback_to(self):
        pass

    async def release(self):
        pass


class SQLiteTransaction(BaseTransaction):

    __slots__ = (
        "engine",
        "context",
        "connection",
        "transaction_type",
        "allow_nested",
        "_savepoint_id",
        "_parent",
        "_committed",
        "_rolled_back",
    )

    def __init__(
        self,
        engine: SQLiteEngine,
        transaction_type: TransactionType = TransactionType.deferred,
        allow_nested: bool = True,
    ):
        """
        :param transaction_type:
            If your transaction just contains ``SELECT`` queries, then use
            ``TransactionType.deferred``. This will give you the best
            performance. When performing ``INSERT``, ``UPDATE``, ``DELETE``
            queries, we recommend using ``TransactionType.immediate`` to
            avoid database locks.
        """
        self.engine = engine
        self.transaction_type = transaction_type
        current_transaction = self.engine.current_transaction.get()

        self._savepoint_id = 0
        self._parent = None
        self._committed = False
        self._rolled_back = False

        if current_transaction:
            if allow_nested:
                self._parent = current_transaction
            else:
                raise TransactionError(
                    "A transaction is already active - nested transactions "
                    "aren't allowed."
                )

    async def __aenter__(self) -> SQLiteTransaction:
        if self._parent is not None:
            return self._parent

        self.connection = await self.get_connection()
        await self.begin()
        self.context = self.engine.current_transaction.set(self)
        return self

    async def get_connection(self):
        return await self.engine.get_connection()

    async def begin(self):
        pass

    async def commit(self):
        await self.connection.execute("COMMIT")
        self._committed = True

    async def rollback(self):
        pass

    async def rollback_to(self, savepoint_name: str):
        pass


    def get_savepoint_id(self) -> int:
        pass

    async def savepoint(self, name: Optional[str] = None) -> Savepoint:
        pass


    async def __aexit__(self, exception_type, exception, traceback) -> bool:
        if self._parent:
            return exception is None

        if exception:
            if not self._rolled_back:
                await self.rollback()
        else:
            if not self._committed and not self._rolled_back:
                await self.commit()

        await self.connection.close()
        self.engine.current_transaction.reset(self.context)

        return exception is None




def dict_factory(cursor, row) -> dict:
    pass


class SQLiteEngine(Engine[SQLiteTransaction]):
    __slots__ = ("connection_kwargs",)

    def __init__(
        self,
        path: str = "piccolo.sqlite",
        log_queries: bool = False,
        log_responses: bool = False,
        **connection_kwargs,
    ) -> None:
        """
        :param path:
            A relative or absolute path to the the SQLite database file (it
            will be created if it doesn't already exist).
        :param log_queries:
            If ``True``, all SQL and DDL statements are printed out before
            being run. Useful for debugging.
        :param log_responses:
            If ``True``, the raw response from each query is printed out.
            Useful for debugging.
        :param connection_kwargs:
            These are passed directly to the database adapter. We recommend
            setting ``timeout`` if you expect your application to process a
            large number of concurrent writes, to prevent queries timing out.
            See Python's `sqlite3 docs <https://docs.python.org/3/library/sqlite3.html#sqlite3.connect>`_
            for more info.

        """  # noqa: E501
        default_connection_kwargs = {
            "database": path,
            "detect_types": sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            "isolation_level": None,
        }

        self.log_queries = log_queries
        self.log_responses = log_responses
        self.connection_kwargs = {
            **default_connection_kwargs,
            **connection_kwargs,
        }

        self.current_transaction = contextvars.ContextVar(
            f"sqlite_current_transaction_{path}", default=None
        )

        super().__init__(
            engine_type="sqlite",
            min_version_number=3.25,
            log_queries=log_queries,
            log_responses=log_responses,
        )

    @property
    def path(self):
        pass

    @path.setter
    def path(self, value: str):
        pass

    async def get_version(self) -> float:
        return self.get_version_sync()

    def get_version_sync(self) -> float:
        major, minor, _ = sqlite3.sqlite_version_info
        return float(f"{major}.{minor}")

    async def prep_database(self):
        pass


    def remove_db_file(self):
        pass

    def create_db_file(self):
        pass


    async def batch(
        self, query: Query, batch_size: int = 100, node: Optional[str] = None
    ) -> AsyncBatch:
        """
        :param query:
            The database query to run.
        :param batch_size:
            How many rows to fetch on each iteration.
        :param node:
            This is ignored currently, as SQLite runs off a single node. The
            value is here so the API is consistent with Postgres.
        """
        connection = await self.get_connection()
        return AsyncBatch(
            connection=connection, query=query, batch_size=batch_size
        )


    async def get_connection(self) -> Connection:
        connection = await aiosqlite.connect(**self.connection_kwargs)
        connection.row_factory = dict_factory  # type: ignore
        await connection.execute("PRAGMA foreign_keys = 1")
        return connection


    async def _get_inserted_pk(self, cursor, table: type[Table]) -> Any:
        """
        If the `pk` column is a non-integer then `ROWID` and `pk` will return
        different types. Need to query by `lastrowid` to get `pk`s in SQLite
        prior to 3.35.0.
        """
        await cursor.execute(
            f"SELECT {table._meta.primary_key._meta.db_column_name} FROM "
            f"{table._meta.tablename} WHERE ROWID = {cursor.lastrowid}"
        )
        response = await cursor.fetchone()
        return response[table._meta.primary_key._meta.db_column_name]

    async def _run_in_new_connection(
        self,
        query: str,
        args: Optional[list[Any]] = None,
        query_type: str = "generic",
        table: Optional[type[Table]] = None,
    ):
        if args is None:
            args = []
        async with aiosqlite.connect(**self.connection_kwargs) as connection:
            await connection.execute("PRAGMA foreign_keys = 1")

            connection.row_factory = dict_factory  # type: ignore
            async with connection.execute(query, args) as cursor:
                await connection.commit()

                if query_type == "insert" and self.get_version_sync() < 3.35:
                    assert table is not None
                    pk = await self._get_inserted_pk(cursor, table)
                    return [{table._meta.primary_key._meta.db_column_name: pk}]
                else:
                    return await cursor.fetchall()

    async def _run_in_existing_connection(
        self,
        connection,
        query: str,
        args: Optional[list[Any]] = None,
        query_type: str = "generic",
        table: Optional[type[Table]] = None,
    ):
        """
        This is used when a transaction is currently active.
        """
        if args is None:
            args = []
        await connection.execute("PRAGMA foreign_keys = 1")

        connection.row_factory = dict_factory
        async with connection.execute(query, args) as cursor:
            response = await cursor.fetchall()

            if query_type == "insert" and self.get_version_sync() < 3.35:
                assert table is not None
                pk = await self._get_inserted_pk(cursor, table)
                return [{table._meta.primary_key._meta.db_column_name: pk}]
            else:
                return response

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = False
    ):
        """
        Connection pools aren't currently supported - the argument is there
        for consistency with other engines.
        """
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=querystring.__str__())

        query, query_args = querystring.compile_string(
            engine_type=self.engine_type
        )

        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await self._run_in_existing_connection(
                connection=current_transaction.connection,
                query=query,
                args=query_args,
                query_type=querystring.query_type,
                table=querystring.table,
            )
        else:
            response = await self._run_in_new_connection(
                query=query,
                args=query_args,
                query_type=querystring.query_type,
                table=querystring.table,
            )

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    async def run_ddl(self, ddl: str, in_pool: bool = False):
        """
        Connection pools aren't currently supported - the argument is there
        for consistency with other engines.
        """
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=ddl)

        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await self._run_in_existing_connection(
                connection=current_transaction.connection,
                query=ddl,
            )
        else:
            response = await self._run_in_new_connection(
                query=ddl,
            )

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    def atomic(
        self, transaction_type: TransactionType = TransactionType.deferred
    ) -> Atomic:
        return Atomic(engine=self, transaction_type=transaction_type)

    def transaction(
        self,
        transaction_type: TransactionType = TransactionType.deferred,
        allow_nested: bool = True,
    ) -> SQLiteTransaction:
        """
        Create a new database transaction. See :class:`Transaction`.
        """
        return SQLiteTransaction(
            engine=self,
            transaction_type=transaction_type,
            allow_nested=allow_nested,
        )
