from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ChatCompletion:
    content: str
    finish_reason: str | None
    raw: dict[str, Any]


class ChatProvider(Protocol):
    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int,
        temperature: float,
    ) -> ChatCompletion:
        ...

