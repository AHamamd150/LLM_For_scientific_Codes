from __future__ import annotations

import importlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import HelperSpec


def normalize_registry(items: Iterable[HelperSpec | dict[str, Any]]) -> list[HelperSpec]:
    registry = [
        item if isinstance(item, HelperSpec) else HelperSpec.from_dict(item)
        for item in items
    ]
    names = [item.name for item in registry]
    if len(names) != len(set(names)):
        raise ValueError("Registry contains duplicate helper names.")

    known = set(names)
    for item in registry:
        unknown = set(item.dependencies) - known
        if unknown:
            raise ValueError(
                f"{item.name} has unknown dependencies: {sorted(unknown)}"
            )
    return registry


def load_registry_json(path: Path) -> list[HelperSpec]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("A registry JSON file must contain a list.")
    return normalize_registry(data)


def load_registry_module(reference: str) -> list[HelperSpec]:
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError("Registry reference must use MODULE:ATTRIBUTE syntax.")
    module = importlib.import_module(module_name)
    return normalize_registry(getattr(module, attribute))

