from __future__ import annotations

import ast


def validate_python_syntax(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return False, f"SyntaxError at line {exc.lineno}: {exc.msg}"
    return True, ""
