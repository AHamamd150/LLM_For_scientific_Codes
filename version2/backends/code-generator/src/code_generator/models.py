from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class GenerationRequest:
    card_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationResult:
    code: str
    raw_responses: tuple[str, ...]
    syntax_valid: bool
    syntax_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "syntax_valid": self.syntax_valid,
            "syntax_error": self.syntax_error,
            "response_count": len(self.raw_responses),
        }


@dataclass(frozen=True)
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0

