from __future__ import annotations

from typing import Protocol

from .model_response import (
    clean_think_blocks,
    extract_python_code,
    looks_incomplete_python,
    merge_code_parts,
)
from .models import GenerationRequest, GenerationResult
from .providers.base import CodeGenerationProvider
from .python_validation import validate_python_syntax


CONTINUE_PROMPT = (
    "Continue the Python script from the next unfinished line only. "
    "Do not restart from the top. Do not repeat completed lines. "
    "Return only raw Python code."
)


class GenerationProfile(Protocol):
    response_rejection_markers: tuple[str, ...]

    def build_messages(self, card_text: str) -> list[dict[str, str]]:
        ...


class CodeGenerator:
    def __init__(
        self,
        provider: CodeGenerationProvider,
        profile: GenerationProfile,
        *,
        allow_continuation: bool = True,
    ) -> None:
        self._provider = provider
        self._profile = profile
        self._allow_continuation = allow_continuation

    def generate(self, request: GenerationRequest) -> GenerationResult:
        messages = self._profile.build_messages(request.card_text)
        raw_first = clean_think_blocks(self._provider.complete(messages))
        first_code = extract_python_code(
            raw_first,
            rejected_markers=self._profile.response_rejection_markers,
        )
        raw_responses = [raw_first]
        final_code = first_code

        if self._allow_continuation and looks_incomplete_python(first_code):
            messages.extend(
                [
                    {"role": "assistant", "content": raw_first},
                    {"role": "user", "content": CONTINUE_PROMPT},
                ]
            )
            raw_second = clean_think_blocks(self._provider.complete(messages))
            raw_responses.append(raw_second)
            final_code = merge_code_parts(
                first_code,
                extract_python_code(
                    raw_second,
                    rejected_markers=self._profile.response_rejection_markers,
                ),
            )

        valid, error = validate_python_syntax(final_code)
        return GenerationResult(
            code=final_code,
            raw_responses=tuple(raw_responses),
            syntax_valid=valid,
            syntax_error=error,
        )
