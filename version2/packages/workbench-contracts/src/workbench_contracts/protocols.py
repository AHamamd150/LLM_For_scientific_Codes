from __future__ import annotations

from typing import Protocol

from .models import CodeArtifact, TaskCard


class CodeGenerator(Protocol):
    def generate(self, card: TaskCard) -> CodeArtifact:
        ...

