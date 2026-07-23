from __future__ import absolute_import, division, print_function

import importlib
import types
from typing import Any


class LazyLoader(types.ModuleType):

    def __init__(self, local_name, parent_module_globals, name):
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals

        super().__init__(name)

    def _load(self) -> types.ModuleType:
        pass

    def __getattr__(self, item) -> Any:
        module = self._load()
        return getattr(module, item)

    def __dir__(self) -> list[str]:
        module = self._load()
        return dir(module)
