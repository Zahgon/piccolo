from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from piccolo.utils.repr import repr_class_instance


class Default(ABC):
    @property
    @abstractmethod
    def postgres(self) -> str:
        pass

    @property
    @abstractmethod
    def sqlite(self) -> str:
        pass

    @abstractmethod
    def python(self) -> Any:
        pass

    def get_postgres_interval_string(self, attributes: list[str]) -> str:
        pass

    def get_sqlite_interval_string(self, attributes: list[str]) -> str:
        pass

    def __repr__(self):
        return repr_class_instance(self)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.__str__())


__all__ = ["Default"]
