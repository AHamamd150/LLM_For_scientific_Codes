# Agentic Code Workbench

[日本語訳](README_ja.md)

A modular workbench for generating Python analysis code from natural-language LHCO analysis cards, executing the code, and reviewing its implemented behavior. It includes an Oracle for identifying unresolved choices in the input, a Helper Selector, a Code Generator, execution and recovery utilities, a Tracer, and a Critique stage.

LHCO-specific prompts, helper metadata, and analysis policies live in `domains/lhco-domain/`. The generic selection, generation, and review components are maintained separately.

## Requirements and setup

Use Python 3.10 or later, Bash, and the following external packages. Run all commands below from the root of the extracted package.

```bash
python -m pip install 'huggingface-hub>=0.27' 'requests>=2.31' numpy matplotlib
```

| Package | Purpose |
| --- | --- |
| `huggingface-hub` | API access for the Helper Selector, Code Generator, and Oracle |
| `requests` | API access for the Tracer and Critique stages |
| `numpy`, `matplotlib` | Numerical processing and plots in generated analysis code |

If needed, create a separate environment first with `python3 -m venv .venv` and `source .venv/bin/activate`. The installation command specifies dependencies rather than a fully pinned environment. To record an experiment, save `python --version` and `python -m pip freeze` from the environment used for the run.

The model providers use the Hugging Face API. Set a token with access to your chosen models. API usage is subject to the provider's terms and charges.

```bash
export HF_TOKEN="your-token"
```

A local Transformers inference runner is not included. The shell scripts below set the required source paths, so editable installation of the individual workbench packages is not required.

## Run one case

Run Case 1 with the supplied data:

```bash
bash scripts/run_qwen3_14b.sh \
  examples/cases/user_input_1.txt \
  data/signal_1.lhco \
  runs/case1
```

The script accepts three arguments:

```bash
bash scripts/run_qwen3_14b.sh CARD LHCO_FILE RUN_DIR
```

| Argument | Meaning |
| --- | --- |
| `CARD` | Input card describing the requested analysis |
| `LHCO_FILE` | LHCO data passed to the generated analysis |
| `RUN_DIR` | Output directory for cards, code, execution records, and reviews |

The script runs these stages:

1. The Helper Selector selects registry helpers and expands their dependencies.
2. The workflow prepares a generation card with `[ADDITIONAL_HELPERS]`.
3. The Code Generator produces Python code, with at most one continuation call per generation if needed.
4. The workflow executes the code. After a failure, it attempts an error-driven fix and, if that fails, regenerates from the generation card.
5. The Tracer extracts the implemented behavior, and Critique compares it with the card.
6. The Oracle reviews the input card after the main workflow and saves a report for a possible next iteration.

`[ADDITIONAL_HELPERS]` provides recommendations; it does not restrict generated code to using only the listed functions.

The default model is `Qwen/Qwen3-14B`, and `MAX_RETRIES` defaults to 3 fix-then-regenerate trials. Each trial executes the fixed code and, if necessary, the regenerated code. Execution attempts are recorded separately.

Generated code can proceed to the Tracer and Critique stages even if execution fails. Check execution success separately from completion of the review stages.

### Change the model

Use `MODEL` rather than duplicating the runner:

```bash
MODEL=Qwen/Qwen3-32B bash scripts/run_qwen3_14b.sh \
  examples/cases/user_input_2.txt \
  data/signal_2.lhco \
  runs/case2_32b
```

This setting applies to the Helper Selector, Code Generator, Fixer, Tracer, Critique, and post-run Oracle. The `14b` in the script name indicates its default model.

The recovery limit can also be changed:

```bash
MAX_RETRIES=2 bash scripts/run_qwen3_14b.sh \
  examples/cases/user_input_1.txt data/signal_1.lhco runs/case1_retry2
```

## Cards and input data

Analysis cards describe the request in `[SELECTION_CUTS]`, `[PLOTS_FOR_VALIDATION]`, and `[OUTPUT_STRUCTURE]`. See `examples/cases/` for examples.

| Case | Analysis | Card | Data |
| --- | --- | --- | --- |
| 1 | W analysis | `user_input_1.txt` | `signal_1.lhco` |
| 2 | Top analysis | `user_input_2.txt` | `signal_2.lhco` |
| 3 | Diphoton analysis | `user_input_3.txt` | `signal_3.lhco` |
| 4 | WZ / trilepton analysis | `user_input_4.txt` | `signal_4.lhco` |
| 5 | VBF H → ττ analysis | `user_input_5.txt` | `signal_5.lhco` |
| 6 | Clarified Case 2 analysis | `user_input_6.txt` | `signal_6.lhco` or `signal_2.lhco` |
| 7 | Clarified Case 5 analysis | `user_input_7.txt` | `signal_7.lhco` or `signal_5.lhco` |

Cards are under `examples/cases/`, and data are under `data/`. Cases 6 and 2 analyze the same process and data using different cards, as do Cases 7 and 5. To avoid symbolic links, `signal_6.lhco` and `signal_7.lhco` are regular-file copies of `signal_2.lhco` and `signal_5.lhco`, respectively.

## Outputs and inspection

| Path under `RUN_DIR` | Contents |
| --- | --- |
| `cards/original.txt` | Card passed to the runner |
| `cards/accepted.txt` | Card supplied to the main workflow |
| `cards/generation.txt` | Generation card incorporating selected helpers |
| `helpers/selection.json`, `summary.txt`, `raw_response.txt` | Helper selections and model response |
| `generation/result.json`, `response_*.txt` | Generation result and initial-generation response records |
| `generation/src/analysis.py` | Generated code; updated during execution recovery |
| `execution/generated_analysis.py` | Most recently executed analysis code |
| `execution/stdout.txt`, `cutflow.txt` | Standard output from a successful execution; `cutflow.txt` is a compatibility copy |
| Plots and other files under `execution/` | Outputs written by generated analysis code |
| `execution/generation_info/` | Code, return codes, standard output, errors, and other records for initial, fix, and regeneration attempts |
| `critique/tracer/final_output.txt` | Tracer's description of the implementation |
| `critique/findings/response_001.txt`, `filtered_review.txt` | Critique results |
| `oracle/request.json`, `user_message.txt`, `response_001.txt` | Post-run Oracle settings, input, and report |

Inspect the cutflow, plots, attempt logs, and the `returncode` / `succeeded` fields in result JSON files under `generation_info/`. Successful execution does not establish physical correctness or conformance to the card. Review the Tracer and Critique outputs as well.

The ordinary runners allow an output directory to be reused. Fixed-name files are overwritten, while old plots or response files that are not produced by the new run may remain. When reusing a directory, inspect the records for the current execution.

## Run all cases and record timing

Use `run_all_timed.sh` in the package root. Start with one run per case:

```bash
bash run_all_timed.sh timing_check 1
```

For ten runs per case, giving 70 case runs:

```bash
bash run_all_timed.sh frozen_timing 10
```

Outputs are saved in directories such as `frozen_timing/run_01/case1/`. Start and end times, elapsed seconds, and status are saved in `frozen_timing/timing_cases1_7.tsv`. The batch script uses `signal_2.lhco` for Case 6 and `signal_5.lhco` for Case 7.

This timing runner rejects an existing output root. Choose a new name if the directory already exists; there is no need to delete previous experiments.

Elapsed time includes the main workflow and post-run Oracle. A TSV status of `success` means that the case runner exited normally; it does not guarantee that the generated analysis executed successfully. Inspect the execution records for each case. The batch script continues with later cases if a case runner fails.

The model can also be changed for the whole batch:

```bash
MODEL=Qwen/Qwen3-32B bash run_all_timed.sh timing_32b 1
```

## Use the Oracle separately

Run an Oracle before generation when you want to review the card first:

```bash
bash scripts/run_oracle_lite.sh \
  examples/cases/user_input_2.txt runs/oracle_lite_case2
```

The report is saved in `runs/oracle_lite_case2/response_001.txt`. Review it, revise the card if needed, and pass the revised card to the generation runner. Oracle reports are never applied to cards automatically.

| Runner | Profile | Default model |
| --- | --- | --- |
| `scripts/run_oracle.sh` | `oracle` | `Qwen/Qwen3-14B` |
| `scripts/run_oracle_lite.sh` | `oracle-lite` | `Qwen/Qwen3-14B` |
| `scripts/run_oracle_lite_extensive.sh` | `oracle-lite-extensive` | `Qwen/Qwen3-14B` |
| `scripts/run_oraclet_8b.sh` | `oraclet` | `Qwen/Qwen3-8B` |

`oracle` combines generic instructions and an output contract with domain context. `oracle-lite` and `oracle-lite-extensive` use single-file prompts. `oraclet` uses a complete prompt supplied by the domain. The name `lite` does not specify model size.

`oracle-lite` filters candidates and reports up to three important unresolved choices. `oracle-lite-extensive` instead prioritizes coverage and reports candidates without a numerical limit; its output requires subsequent review.

To change the model, number of runs, output-token limit, or temperature:

```bash
MODEL=Qwen/Qwen3-32B RUNS=3 MAX_TOKENS=1800 TEMPERATURE=0.2 \
bash scripts/run_oracle_lite.sh \
  examples/cases/user_input_2.txt runs/oracle_lite_case2_32b
```

When using the general runner for the same profile, set `PROFILE=oracle-lite ORACLE_OUTPUT_CONTRACT=none`. Do not append a separate system output contract to `oracle-lite`, `oracle-lite-extensive`, or `oraclet`.

The main generation runner uses `oracle` for its post-run review by default. To change it, pass `ORACLE_PROFILE` and `ORACLE_OUTPUT_CONTRACT` to `run_qwen3_14b.sh`:

```bash
ORACLE_PROFILE=oracle-lite ORACLE_OUTPUT_CONTRACT=none \
bash scripts/run_qwen3_14b.sh \
  examples/cases/user_input_1.txt data/signal_1.lhco runs/case1_lite
```

Older Oracle prompts are stored in `packages/golden-axe-oracle/src/golden_axe/profiles/oldfiles/`. To use an older prompt, replace the corresponding active prompt file with the desired file from that directory.

## Tests

```bash
bash scripts/test_all.sh
```

The component and integration tests use mock providers; no model downloads or API access are required. For a real-model check, run one case first, then use `run_all_timed.sh` for one run of each case.

## Optional: rerun only Tracer and Critique

`scripts/run_qwen3_32b_postreview.sh` is an additional experimental utility that reuses existing analysis code and reruns only Tracer and Critique, using a 32B model by default. These postreview experiments were not included in the paper. The utility does not regenerate or execute the analysis code.

```bash
bash scripts/run_qwen3_32b_postreview.sh 2 7
```

This reads `examples/cases/user_input_2.txt` and `frozen_timing/run_07/case2/execution/generated_analysis.py`, and writes to `critique_qwen3_32b/` under that case directory. The script rejects an existing output directory. If the input data have been moved elsewhere, adjust the script paths to their current locations.

For arbitrary existing code, the review CLI can also be used directly:

```bash
PYTHONPATH=packages/critique-pipeline/src \
python -m critique_pipeline.cli run \
  --card runs/case1/cards/generation.txt \
  --code runs/case1/execution/generated_analysis.py \
  --tracer-model Qwen/Qwen3-32B \
  --critique-model Qwen/Qwen3-32B \
  --domain-context domains/lhco-domain/src/lhco_domain/prompts/critique_context.txt \
  --n-runs 1 --no-repair \
  --run-dir runs/case1/postreview_32b
```

## Optional: evaluate Tracer fidelity

`scripts/evaluate_tracer.py` reads a task card, generated code, and Tracer output. It evaluates requirement coverage, source references, dependencies, and hallucinations, and saves the results as CSV. This is separate from Critique and does not judge the physical correctness of the generated analysis.

This utility uses the OpenAI API. Install its additional dependency and set the API key:

```bash
python -m pip install openai
export OPENAI_API_KEY="your-key"
```

Set `EVALUATION_MODEL` to the model you want to use. The script uses the Responses API with `reasoning.effort=low`, so choose a model that supports those settings.

```bash
python scripts/evaluate_tracer.py \
  --case 1 --run 1 \
  --task-card examples/cases/user_input_1.txt \
  --code runs/case1/execution/generated_analysis.py \
  --trace runs/case1/critique/tracer/final_output.txt \
  --model "${EVALUATION_MODEL:?Set EVALUATION_MODEL}" \
  --out tracer_evaluation_check/case1_run01.csv
```

`--case` and `--run` label CSV records; the input paths are provided explicitly. The output contains per-requirement evaluations and unsupported extra Tracer claims. Review the evaluations before using them.

## Directory layout

| Path | Role |
| --- | --- |
| `packages/workbench-contracts/` | Shared types, artifact layout, and protocols |
| `packages/helper-selector/` | Helper selection and dependency expansion |
| `packages/golden-axe-oracle/` | Review of unresolved choices in the input |
| `packages/critique-pipeline/` | Tracer and Critique |
| `backends/code-generator/` | Generic generation, continuation, execution, and fixing |
| `domains/lhco-domain/` | LHCO card parsing, prompts, registry, and policies |
| `domains/dummy-domain/` | Small fixture for domain-swap tests |
| `workflows/` | Composition of stages after card acceptance |
| `scripts/` | Single-run, Oracle, test, and additional evaluation entry points |
| `examples/cases/` | Example analysis cards |
| `data/` | LHCO input data |
| `paper_data/`, `recalculation/` | Preserved paper experiment and recalculation materials |
| `tests/` | Integration tests |
| `run_all_timed.sh` | Batch execution and timing |
| `README/` | Historical architecture and development documents |

The active registry favors composing low-level helpers using explicitly selected objects and collections. Some older helpers that re-extract objects from whole events are excluded from the default selection registry. The legacy registry is retained in `registry_legacy.py`, and the legacy generation prompt in `prompts/codegen_system_legacy.txt`.

`paper_data/` and `recalculation/` preserve paper materials. Do not delete or initialize them when running tests or starting new experiments. Store new runs in separate output locations so they remain distinguishable from the published results.

The former Streamlit GUI and MLP/GNN/Transformer applications are outside the scope of this code-generation workbench.
