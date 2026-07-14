from __future__ import annotations

import json
from pathlib import Path

from .models import SelectionResult


def write_selection(result: SelectionResult, path: Path) -> None:
    path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def read_selection(path: Path) -> SelectionResult:
    return SelectionResult.from_dict(
        json.loads(path.read_text(encoding="utf-8"))
    )


def write_summary(result: SelectionResult, path: Path) -> None:
    lines = ["# Selected helpers", ""]
    for item in result.selected_helpers:
        suffix = f": {item.reason}" if item.reason else ""
        lines.append(f"- {item.name}{suffix}")
    lines.extend(["", "# Rejected but close", ""])
    for item in result.rejected_but_close:
        suffix = f": {item.reason}" if item.reason else ""
        lines.append(f"- {item.name}{suffix}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

