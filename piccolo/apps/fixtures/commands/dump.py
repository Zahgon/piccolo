from __future__ import annotations

from typing import Any, Optional

from piccolo.apps.fixtures.commands.shared import (
    FixtureConfig,
    create_pydantic_fixture_model,
)
from piccolo.conf.apps import Finder
from piccolo.table import sort_table_classes


async def get_dump(
    fixture_configs: list[FixtureConfig],
) -> dict[str, Any]:
    """
    Gets the data for each table specified and returns a data structure like:

    .. code-block:: python

        {
            'my_app_name': {
                'MyTableName': [
                    {
                        'id': 1,
                        'my_column_name': 'foo'
                    }
                ]
            }
        }

    """
    finder = Finder()

    output: dict[str, Any] = {}

    for fixture_config in fixture_configs:
        app_config = finder.get_app_config(app_name=fixture_config.app_name)
        table_classes = [
            i
            for i in app_config.table_classes
            if i.__name__ in fixture_config.table_class_names
        ]
        sorted_table_classes = sort_table_classes(table_classes)

        output[fixture_config.app_name] = {}

        for table_class in sorted_table_classes:
            data = await table_class.select().order_by(
                table_class._meta.primary_key
            )
            output[fixture_config.app_name][table_class.__name__] = data

    return output


async def dump_to_json_string(
    fixture_configs: list[FixtureConfig],
) -> str:
    """
    Dumps all of the data for the given tables into a JSON string.
    """
    dump = await get_dump(fixture_configs=fixture_configs)
    pydantic_model = create_pydantic_fixture_model(
        fixture_configs=fixture_configs
    )
    return pydantic_model(**dump).model_dump_json(indent=4)


def parse_args(apps: str, tables: str) -> list[FixtureConfig]:
    pass


async def dump(apps: str = "all", tables: str = "all"):
    pass
