from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HelperSpec:
    name: str
    section: str
    summary: str
    keywords: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HelperSpec":
        return cls(
            name=str(data["name"]),
            section=str(data["section"]),
            summary=str(data["summary"]),
            keywords=tuple(str(value) for value in data["keywords"]),
            aliases=tuple(str(value) for value in data.get("aliases", ())),
            dependencies=tuple(str(value) for value in data.get("dependencies", ())),
        )


@dataclass(frozen=True)
class SelectionItem:
    name: str
    reason: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectionItem":
        return cls(name=str(data["name"]), reason=str(data.get("reason", "")))


@dataclass(frozen=True)
class SelectionResult:
    selected_helpers: tuple[SelectionItem, ...]
    rejected_but_close: tuple[SelectionItem, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_helpers": [asdict(item) for item in self.selected_helpers],
            "rejected_but_close": [
                asdict(item) for item in self.rejected_but_close
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SelectionResult":
        return cls(
            selected_helpers=tuple(
                SelectionItem.from_dict(item)
                for item in data.get("selected_helpers", ())
            ),
            rejected_but_close=tuple(
                SelectionItem.from_dict(item)
                for item in data.get("rejected_but_close", ())
            ),
        )

