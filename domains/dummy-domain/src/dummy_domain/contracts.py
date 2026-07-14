from __future__ import annotations

from workbench_contracts import GeneratedScriptIOContract


DUMMY_IO_CONTRACT = GeneratedScriptIOContract(
    input_argument="sys.argv[1:]",
    input_format=(
        "One or more UTF-8 text files, each containing one number per non-empty line. "
        "Lines may contain integers or floating-point values."
    ),
    output_location=(
        "the current working directory.  The workflow sets this to "
        "RUN_DIR/execution before running the generated script."
    ),
    stdout_summary=(
        "print a concise text summary with at least the number count and sum. "
        "The workflow stores stdout as execution/stdout.txt."
    ),
    required_outputs=(
        "result.txt containing the numeric sum followed by a newline",
    ),
)
