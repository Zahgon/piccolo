from __future__ import annotations

from typing import Any

try:
    import orjson

    ORJSON = True
except ImportError:
    import json

    ORJSON = False


def dump_json(data: Any, pretty: bool = False) -> str:
    if ORJSON:
        orjson_params: dict[str, Any] = {"default": str}
        if pretty:
            orjson_params["option"] = (
                orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE  # type: ignore
            )
        return orjson.dumps(data, **orjson_params).decode(  # type: ignore
            "utf8"
        )
    else:
        params: dict[str, Any] = {"default": str}
        if pretty:
            params["indent"] = 2
        return json.dumps(data, **params)  # type: ignore


class JSONDict(dict):

    ...


def load_json(data: str | bytes | bytearray) -> Any:
    response = (
        orjson.loads(data) if ORJSON else json.loads(data)  # type: ignore
    )

    if isinstance(response, dict):
        return JSONDict(**response)

    return response
