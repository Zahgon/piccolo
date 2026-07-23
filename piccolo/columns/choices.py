from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Choice:

    value: Any
    display_name: str
