from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunLayout:
    root: Path

    @property
    def cards(self) -> Path:
        return self.root / "cards"

    @property
    def oracle(self) -> Path:
        return self.root / "oracle"

    @property
    def helpers(self) -> Path:
        return self.root / "helpers"

    @property
    def generation(self) -> Path:
        return self.root / "generation"

    @property
    def execution(self) -> Path:
        return self.root / "execution"

    @property
    def execution_info(self) -> Path:
        return self.execution / "generation_info"

    @property
    def critique(self) -> Path:
        return self.root / "critique"

    def create(self) -> None:
        for path in (
            self.cards,
            self.oracle,
            self.helpers,
            self.generation,
            self.execution,
            self.execution_info,
            self.critique,
        ):
            path.mkdir(parents=True, exist_ok=True)
