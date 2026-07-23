from collections.abc import Sequence
from typing import Optional

from piccolo.columns.base import Column
from piccolo.querystring import QueryString

from .base import Function


class Avg(Function):

    function_name = "AVG"


class Count(QueryString):

    def __init__(
        self,
        column: Optional[Column] = None,
        distinct: Optional[Sequence[Column]] = None,
        alias: str = "count",
    ):
        """
        :param column:
            If specified, the count is for non-null values in that column.
        :param distinct:
            If specified, the count is for distinct values in those columns.
        :param alias:
            The name of the value in the response::

                # These two are equivalent:

                await Band.select(
                    Band.name, Count(alias="total")
                ).group_by(Band.name)

                await Band.select(
                    Band.name,
                    Count().as_alias("total")
                ).group_by(Band.name)

        """
        if distinct and column:
            raise ValueError("Only specify `column` or `distinct`")

        if distinct:
            engine_type = distinct[0]._meta.engine_type
            if engine_type == "sqlite":
                column_names = " || ".join("{}" for _ in distinct)
            else:
                column_names = ", ".join("{}" for _ in distinct)

            return super().__init__(
                f"COUNT(DISTINCT({column_names}))", *distinct, alias=alias
            )
        else:
            if column:
                return super().__init__("COUNT({})", column, alias=alias)
            else:
                return super().__init__("COUNT(*)", alias=alias)


class Min(Function):

    function_name = "MIN"


class Max(Function):

    function_name = "MAX"


class Sum(Function):

    function_name = "SUM"


__all__ = (
    "Avg",
    "Count",
    "Min",
    "Max",
    "Sum",
)
