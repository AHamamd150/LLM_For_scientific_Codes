from __future__ import annotations

import re


def clean_think_blocks(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_python_code(
    text: str,
    *,
    rejected_markers: tuple[str, ...] = (),
) -> str:
    if not text or not text.strip():
        return ""
    stripped = text.strip()
    python_blocks = re.findall(
        r"```python\s*\n?(.*?)```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if python_blocks:
        return max(python_blocks, key=len).strip()
    generic_blocks = re.findall(r"```\s*\n?(.*?)```", stripped, re.DOTALL)
    if generic_blocks:
        return max(generic_blocks, key=len).strip()

    for pattern in (
        r"^#!/usr/bin/env python",
        r"^import\s+sys\b",
        r"^import\s+math\b",
        r'^"""',
        r"^'''",
    ):
        match = re.search(pattern, stripped, re.MULTILINE)
        if match:
            lines: list[str] = []
            for line in stripped[match.start() :].splitlines():
                if line.strip().startswith(
                    ("Human:", "H:", "Assistant:", "A:", "###")
                ):
                    break
                lines.append(line)
            return "\n".join(lines).strip()

    if "Human:" in stripped or stripped.startswith("H:"):
        return ""
    if any(marker in stripped[:100] for marker in rejected_markers):
        return ""
    return stripped


def looks_incomplete_python(code: str) -> bool:
    stripped = code.rstrip()
    if not stripped:
        return True
    if stripped.endswith((":", "\\", "(", "[", "{", ",")):
        return True
    for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
        if stripped.count(opening) != stripped.count(closing):
            return True
    return False


def merge_code_parts(first: str, second: str) -> str:
    first_lines = first.rstrip().splitlines()
    second_lines = second.lstrip().splitlines()
    if (
        first_lines
        and second_lines
        and first_lines[-1].rstrip().endswith(":")
        and second_lines[0]
        and not second_lines[0][0].isspace()
    ):
        base_indent = len(first_lines[-1]) - len(first_lines[-1].lstrip())
        second_lines[0] = " " * (base_indent + 4) + second_lines[0]
    max_overlap = min(len(first_lines), len(second_lines))
    for size in range(max_overlap, 0, -1):
        if first_lines[-size:] == second_lines[:size]:
            return "\n".join(first_lines + second_lines[size:]).strip()
    return "\n".join(first_lines + second_lines).strip()
