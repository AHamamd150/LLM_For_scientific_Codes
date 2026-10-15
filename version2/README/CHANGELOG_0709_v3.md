# 0709 v3 changes

Scope: provisional I/O contract cleanup only.  This release does not change
helper selection, default-helper domain assets, tracer, critique, or oracle logic.

## Changes

- Workflow CLI now accepts one or more input files with a single `--input` option:
  - `--input file1.lhco`
  - `--input file1.lhco file2.lhco ...`
- Workflow execution passes all input paths to the generated script as command-line
  arguments after the script name.
- Workflow pipeline rejects input files placed under the run directory before code
  generation/execution proceeds.
- The pipeline keeps backward-compatible `input_path` handling for direct Python
  callers, but the preferred interface is now `input_paths`.
- LHCO generation profile now instructs generated scripts to read input paths from
  `sys.argv[1:]`, process all provided LHCO files, and concatenate the events.
- LHCO generation profile now instructs generated scripts to write output files
  using relative paths and to print cutflow/numerical summaries to stdout.
- Dummy example domain and typed I/O contract were updated from `sys.argv[1]` to
  `sys.argv[1:]`.

## Tests

- Full test suite passed: `61 passed`.
