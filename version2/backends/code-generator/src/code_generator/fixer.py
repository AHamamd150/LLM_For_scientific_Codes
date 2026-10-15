from __future__ import annotations

from .model_response import clean_think_blocks, extract_python_code
from .providers.base import CodeGenerationProvider


FIX_SYSTEM_PROMPT = """/no_think

You are an expert Python debugger. Fix the supplied Python code from the
traceback. Return the complete fixed code, preserve the original functionality,
and output only raw Python code without explanations or Markdown fences."""


def build_fix_messages(code: str, error: str) -> list[dict[str, str]]:
    numbered = "\n".join(
        f"{index:4d} | {line}"
        for index, line in enumerate(code.splitlines(), start=1)
    )
    return [
        {"role": "system", "content": FIX_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Fix this Python code:\n\n"
                f"## Code\n{numbered}\n\n"
                f"## Full traceback\n{error}\n\n"
                "Return the complete fixed code without line numbers."
            ),
        },
    ]


def fix_code(
    code: str,
    error: str,
    provider: CodeGenerationProvider,
) -> tuple[str, str]:
    raw = clean_think_blocks(
        provider.complete(build_fix_messages(code, error))
    )
    return extract_python_code(raw), raw
