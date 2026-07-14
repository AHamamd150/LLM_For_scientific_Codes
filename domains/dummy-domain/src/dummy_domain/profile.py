from __future__ import annotations

from importlib.resources import files

from .contracts import DUMMY_IO_CONTRACT


def _load_prompt(name: str) -> str:
    return files("dummy_domain").joinpath(
        "prompts", f"{name}.txt"
    ).read_text(encoding="utf-8")


def load_codegen_system_prompt() -> str:
    return _load_prompt("codegen_system").replace(
        "{{ GENERATED_SCRIPT_IO_CONTRACT }}",
        DUMMY_IO_CONTRACT.to_prompt_text(),
    )


def load_critique_context() -> str:
    return _load_prompt("critique_context")


def load_oracle_context() -> str:
    return _load_prompt("oracle_context")


def load_helper_policy() -> str:
    return _load_prompt("helper_policy")


class DummyGenerationProfile:
    response_rejection_markers = ()

    def __init__(self, *, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt

    def build_messages(self, card_text: str) -> list[dict[str, str]]:
        system_prompt = self._system_prompt or load_codegen_system_prompt()
        return [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": card_text,
            },
        ]


DUMMY_PROFILE = DummyGenerationProfile()
