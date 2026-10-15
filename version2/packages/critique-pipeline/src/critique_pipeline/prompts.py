from __future__ import annotations

from importlib.resources import files


def load_prompt(name: str) -> str:
    allowed = {
        "tracer_system_prompt",
        "trace_code",
        "critique_system_prompt",
        "critique_output_rules",
    }
    if name not in allowed:
        raise ValueError(f"Unknown prompt {name!r}.")
    return files("critique_pipeline").joinpath(
        "prompts", f"{name}.txt"
    ).read_text(encoding="utf-8")
