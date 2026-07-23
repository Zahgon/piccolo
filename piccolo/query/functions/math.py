
from .base import Function


class Abs(Function):

    function_name = "ABS"


class Ceil(Function):

    function_name = "CEIL"


class Floor(Function):

    function_name = "FLOOR"


class Round(Function):

    function_name = "ROUND"


__all__ = (
    "Abs",
    "Ceil",
    "Floor",
    "Round",
)
