from __future__ import annotations

import importlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def _field(item: Any, name: str, default: Any = "") -> Any:
    if isinstance(item, Mapping):
        return item.get(name, default)
    return getattr(item, name, default)


def render_registry(items: Iterable[Any]) -> str:
    blocks: list[str] = []
    for item in items:
        keywords = _field(item, "keywords", ())
        aliases = _field(item, "aliases", ())
        lines = [
            f"- name: {_field(item, 'name')}",
            f"  section: {_field(item, 'section')}",
            f"  summary: {_field(item, 'summary')}",
            f"  keywords: {', '.join(str(value) for value in keywords)}",
        ]
        if aliases:
            lines.append(
                f"  aliases: {', '.join(str(value) for value in aliases)}"
            )
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def load_registry_json(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("A registry JSON file must contain a list.")
    return render_registry(data)


def load_registry_module(reference: str) -> str:
    module_name, separator, attribute = reference.partition(":")
    if not separator:
        raise ValueError("Registry reference must use MODULE:ATTRIBUTE syntax.")
    module = importlib.import_module(module_name)
    return render_registry(getattr(module, attribute))

