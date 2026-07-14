from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .models import ExecutionResult


def execute_python(
    script_path: Path,
    arguments: list[str],
    *,
    working_directory: Path,
    timeout: int = 300,
) -> ExecutionResult:
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    result = subprocess.run(
        [sys.executable, str(script_path), *arguments],
        cwd=working_directory,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return ExecutionResult(
        returncode=result.returncode,
        stdout=result.stdout or "",
        stderr=result.stderr or "",
    )

