# Oracle usage guide

This note explains how to run the oracle-related checks in the stable package.
It replaces the short stable changelog and includes the usability changes that were added for oracle experiments.

## What is included in this stable package

This package is based on the July 10 safe-codegen version and adds the following oracle usability files.

- `scripts/run_oracle.sh`
  - General oracle runner.
  - Handles profiles without an oracle context safely, including on macOS bash.
- `scripts/run_oracle_lite.sh`
  - Convenience wrapper for the `oracle_lite` profile.
  - Defaults to `MODEL=Qwen/Qwen3-14B`, `PROFILE=oracle_lite`, and `ORACLE_OUTPUT_CONTRACT=none`.
- `scripts/run_oraclet_8b.sh`
  - Convenience wrapper for the `oraclet` profile with Qwen3-8B.
  - Defaults to `MODEL=Qwen/Qwen3-8B`, `PROFILE=oraclet`, and `ORACLE_OUTPUT_CONTRACT=none`.
- `examples/cases/user_input_5_legacy.txt`
  - Legacy version of case 5, before the explicit `ditau_obj` / `dijet_obj` rewrite.

## Before running

Set your Hugging Face token in the shell.

```bash
export HF_TOKEN=...
```

Run commands from the package root directory.

```bash
cd agentic-code-workbench_stable
```

Each runner takes two positional arguments.

```bash
./scripts/<runner>.sh CARD RUN_DIR
```

The oracle output is written to:

```text
RUN_DIR/response_001.txt
```

## Recommended card-ambiguity check: oracle-lite

Use `oracle_lite` when you want a lightweight ambiguity check of an analysis card before running the full generation pipeline.

```bash
./scripts/run_oracle_lite.sh examples/cases/user_input_5.txt run_oracle_lite_case5
```

To run the legacy case 5 card:

```bash
./scripts/run_oracle_lite.sh examples/cases/user_input_5_legacy.txt run_oracle_lite_case5_legacy
```

The wrapper sets:

```bash
PROFILE=oracle_lite
ORACLE_OUTPUT_CONTRACT=none
MODEL=Qwen/Qwen3-14B
```

`ORACLE_OUTPUT_CONTRACT=none` is intentional. The `oracle_lite` profile is a complete prompt and should not receive an additional system output contract.

To try a larger model, override `MODEL` at the command line.

```bash
MODEL=Qwen/Qwen3-32B \
./scripts/run_oracle_lite.sh examples/cases/user_input_5.txt run_oracle_lite_32b_case5
```

To try an 8B model:

```bash
MODEL=Qwen/Qwen3-8B \
./scripts/run_oracle_lite.sh examples/cases/user_input_5.txt run_oracle_lite_8b_case5
```

## Structured 8B oracle: oraclet

Use `oraclet` when you want to test the smaller, more structured oracle profile originally intended for Qwen3-8B.

```bash
./scripts/run_oraclet_8b.sh examples/cases/user_input_5.txt run_oraclet_8b_case5
```

The wrapper sets:

```bash
MODEL=Qwen/Qwen3-8B
PROFILE=oraclet
ORACLE_OUTPUT_CONTRACT=none
```

`ORACLE_OUTPUT_CONTRACT=none` is also intentional here. The `oraclet` profile is a complete/domain-owned prompt and should not receive an additional system output contract.

To compare `oraclet` with a 14B or 32B model, override `MODEL`.

```bash
MODEL=Qwen/Qwen3-14B \
./scripts/run_oraclet_8b.sh examples/cases/user_input_5.txt run_oraclet_14b_case5
```

```bash
MODEL=Qwen/Qwen3-32B \
./scripts/run_oraclet_8b.sh examples/cases/user_input_5.txt run_oraclet_32b_case5
```

## General oracle runner

The low-level runner remains available for manual experiments.

```bash
PROFILE=oracle \
ORACLE_OUTPUT_CONTRACT=system \
RUNS=1 \
MAX_TOKENS=1800 \
TEMPERATURE=0.2 \
./scripts/run_oracle.sh examples/cases/user_input_5.txt run_oracle_case5
```

The useful combinations are:

| Profile | Typical model | Output contract | Notes |
|---|---:|---|---|
| `oracle` | Qwen3-14B | `system`, `domain`, or `auto` | General oracle profile. |
| `oracle_lite` | Qwen3-14B or Qwen3-32B | `none` | Lightweight card ambiguity checker. |
| `oraclet` | Qwen3-8B | `none` | Structured profile for smaller models. |

Avoid these combinations:

```bash
PROFILE=oracle_lite ORACLE_OUTPUT_CONTRACT=system
PROFILE=oraclet      ORACLE_OUTPUT_CONTRACT=system
```

Both profiles are complete prompts, so adding a separate system output contract will raise an error.

## Suggested comparison runs for case 5

```bash
./scripts/run_oracle_lite.sh examples/cases/user_input_5.txt run_lite_14b_case5
```

```bash
MODEL=Qwen/Qwen3-32B \
./scripts/run_oracle_lite.sh examples/cases/user_input_5.txt run_lite_32b_case5
```

```bash
./scripts/run_oraclet_8b.sh examples/cases/user_input_5.txt run_oraclet_8b_case5
```

```bash
./scripts/run_oracle_lite.sh examples/cases/user_input_5_legacy.txt run_lite_14b_case5_legacy
```

## Interpreting oracle-lite output

For each ambiguity, check whether the suggestion is actually useful for the domain card.

Useful findings often include:

- unclear selected-object scope,
- unclear composite-object definition,
- ambiguous reuse of a named system such as `ditau_obj`, `dijet_obj`, `diphoton_obj`, or `trilepton_obj`,
- unclear meaning of a plotted observable.

Be cautious about findings that are mostly implementation style rather than card ambiguity, such as asking to store intermediate objects as event-level objects or changing cutflow timing without a real ambiguity.

## Case 5 note

The current case 5 card explicitly defines `ditau_obj` and `dijet_obj`. The legacy version keeps the older wording:

```text
Build ditau system from the leading tau and subleading tau.
Build dijet system from the leading jet and subleading jet.
```

The legacy card is useful for checking whether an oracle profile catches the ambiguity that later observables should use the same composite systems rather than recomputing from constituents or using event-level helper shortcuts.
