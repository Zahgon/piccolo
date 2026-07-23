import uuid
from collections.abc import Callable
from enum import Enum
from typing import Union

from piccolo.utils.uuid import uuid7

from .base import Default


class UUID4(Default):

    @property
    def postgres(self):
        pass

    @property
    def cockroach(self):
        pass

    @property
    def sqlite(self):
        pass

    def python(self):
        pass


class UUID7(Default):

    @property
    def postgres(self):
        pass

    @property
    def cockroach(self):
        pass

    @property
    def sqlite(self):
        pass

    def python(self):
        pass


UUIDArg = Union[
    UUID4,
    UUID7,
    uuid.UUID,
    str,
    Enum,
    None,
    Callable[[], uuid.UUID],
]


__all__ = ["UUIDArg", "UUID4", "UUID7"]
