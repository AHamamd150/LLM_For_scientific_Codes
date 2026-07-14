from __future__ import annotations

from typing import Protocol


class CodeGenerationProvider(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str:
        ...

