from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class OracleRequest:
    card_text: str
    registry_text: str = ""
    codegen_system_prompt: str = ""
    profile: str = "oracle"

    def to_manifest(self) -> dict[str, Any]:
        manifest = asdict(self)
        manifest.pop("card_text")
        manifest.pop("registry_text")
        manifest.pop("codegen_system_prompt")
        return manifest


@dataclass(frozen=True)
class OracleResponse:
    text: str
    profile: str
