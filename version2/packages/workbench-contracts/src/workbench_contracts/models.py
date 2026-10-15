from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedScriptIOContract:
    """Human-readable contract between the workflow and generated scripts.

    The current workflow executes generated Python scripts as standalone
    programs.  Domains should expose an instance of this type so users can see
    how the generated script receives input and where outputs should go.
    """

    input_argument: str
    input_format: str
    output_location: str
    stdout_summary: str
    required_outputs: tuple[str, ...] = ()

    def to_prompt_text(self) -> str:
        lines = [
            "Generated script I/O contract:",
            f"- Input argument: {self.input_argument}",
            f"- Input format: {self.input_format}",
            f"- Output location: {self.output_location}",
            f"- Standard output: {self.stdout_summary}",
        ]
        if self.required_outputs:
            lines.append("- Required output files:")
            lines.extend(f"  - {item}" for item in self.required_outputs)
        return "\n".join(lines)


@dataclass(frozen=True)
class TaskCard:
    text: str
    source_name: str = "card.txt"


@dataclass(frozen=True)
class CodeArtifact:
    code: str
    language: str = "python"
    filename: str = "analysis.py"
