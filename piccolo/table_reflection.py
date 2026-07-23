
import asyncio
from dataclasses import dataclass
from typing import Any, Optional, Union

from piccolo.apps.schema.commands.generate import get_output_schema
from piccolo.engine import engine_finder
from piccolo.engine.base import Engine
from piccolo.table import Table


class Immutable(object):
    def _immutable(self, *args, **kwargs) -> TypeError:
        raise TypeError("%s object is immutable" % self.__class__.__name__)

    __delitem__ = __setitem__ = __setattr__ = _immutable  # type: ignore


class ImmutableDict(Immutable, dict):  # type: ignore

    clear = pop = popitem = setdefault = update = Immutable._immutable  # type: ignore  # noqa: E501

    def __new__(cls, *args):
        return dict.__new__(cls)

    def copy(self):
        raise NotImplementedError(
            "an immutabledict shouldn't need to be copied.  use dict(d) "
            "if you need a mutable dictionary."
        )

    def __reduce__(self):
        return ImmutableDict, (dict(self),)

    def _insert_item(self, key, value) -> None:
        pass

    def _delete_item(self, key) -> None:
        pass

    def __repr__(self):
        return f"ImmutableDict({dict.__repr__(self)})"


class Singleton(type):

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


@dataclass
class TableNameDetail:
    name: str = ""
    schema: str = ""


class TableStorage(metaclass=Singleton):

    def __init__(self, engine: Optional[Engine] = None):
        """
        :param engine:
            Which engine to use to make the database queries. If not specified,
            we try importing an engine from ``piccolo_conf.py``.

        """
        self.engine = engine or engine_finder()
        self.tables = ImmutableDict()
        self._schema_tables: dict[str, list[str]] = {}

    async def reflect(
        self,
        schema_name: str = "public",
        include: Union[list[str], str, None] = None,
        exclude: Union[list[str], str, None] = None,
        keep_existing: bool = False,
    ) -> None:
        pass

    def clear(self) -> None:
        pass

    async def get_table(self, tablename: str) -> Optional[type[Table]]:
        pass

    async def _add_table(self, schema_name: str, table: type[Table]) -> None:
        pass

    def _add_to_schema_tables(self, schema_name: str, table_name: str) -> None:
        pass

    @staticmethod
    def _get_table_name(name: str, schema: str):
        pass

    def __repr__(self):
        return f"{[tablename for tablename, _ in self.tables.items()]}"

    @staticmethod
    def _get_schema_and_table_name(tablename: str) -> TableNameDetail:
        pass

    @staticmethod
    def _to_list(value: Any) -> list:
        pass
