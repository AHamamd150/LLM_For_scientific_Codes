# Optional scripts: execution check guide

## Scope

This guide describes how to check the optional review and evaluation utilities using an existing Case 1 run. It assumes that the main generation workflow has already produced analysis code and a Tracer output with the default 14B model. There is no need to rerun all seven cases or recalculate the paper results.

The commands below are provided as an execution guide; the API calls in this guide were not executed during its preparation.

The suggested order is:

1. Rerun only Tracer and Critique with a 32B model on the existing code.
2. Evaluate the original 14B Tracer output using `evaluate_tracer.py`.
3. Evaluate the new 32B Tracer output using the same evaluation model.

This checks the utilities and their inputs and outputs. A single run is not a model-performance comparison.

## 0. Preparation

Activate the Python environment prepared according to the README. Run all commands from the package root, in the same shell session so that the variables remain available.

Set the directory containing a completed main-workflow run:

```bash
CHECK_RUN=runs/clean_check_case1
```

Change this variable if your completed run is stored elsewhere. Confirm that these four input files exist:

```bash
ls "$CHECK_RUN/cards/accepted.txt" \
   "$CHECK_RUN/cards/generation.txt" \
   "$CHECK_RUN/execution/generated_analysis.py" \
   "$CHECK_RUN/critique/tracer/final_output.txt"
```

Step 1 requires the Hugging Face credentials (`HF_TOKEN`) used for the main workflow. Steps 2 and 3 require OpenAI API credentials and an additional package:

```bash
python -m pip install openai
export OPENAI_API_KEY="your-key"
```

The default evaluation model in `evaluate_tracer.py` is `gpt-5.6-luna`. Set `EVALUATION_MODEL` to override it. The script uses the Responses API with `reasoning.effort=low`; select an available model supporting those settings. Current availability of the default model was not verified in preparing this guide. These operations use the respective providers' APIs and may incur charges.

## 1. Rerun only Tracer and Critique with a 32B model

`run_qwen3_32b_postreview.sh` has fixed input paths under `frozen_timing/`. For an existing run stored elsewhere, use the review CLI directly. There is no need to copy results into the wrapper's expected directory layout.

```bash
PYTHONPATH=packages/critique-pipeline/src \
python -m critique_pipeline.cli run \
  --card "$CHECK_RUN/cards/generation.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --tracer-model Qwen/Qwen3-32B \
  --critique-model Qwen/Qwen3-32B \
  --domain-context domains/lhco-domain/src/lhco_domain/prompts/critique_context.txt \
  --n-runs 1 --no-repair \
  --run-dir "$CHECK_RUN/postreview_32b_check"
```

This uses the Hugging Face API. It does not regenerate or execute the analysis code, and it writes the new review to a separate directory, leaving the original Tracer and Critique outputs in place. Choose a new review directory when you want to preserve an earlier check.

After completion, confirm that the following outputs exist:

```bash
ls "$CHECK_RUN/postreview_32b_check/tracer/final_output.txt" \
   "$CHECK_RUN/postreview_32b_check/critique/response_001.txt" \
   "$CHECK_RUN/postreview_32b_check/critique/filtered_review.txt"
```

The standalone review CLI writes Critique results under `critique/`; the main generation workflow uses `critique/findings/`.

### Alternative: check the postreview wrapper itself

If the required analysis code already exists at `frozen_timing/run_01/case1/execution/generated_analysis.py`, the wrapper can instead be checked with:

```bash
bash scripts/run_qwen3_32b_postreview.sh 1 1
```

It reads the Case 1 example card and writes to `frozen_timing/run_01/case1/critique_qwen3_32b/`. It refuses to overwrite an existing output directory. If historical inputs have been moved to `paper_data/`, inspect and adjust the wrapper's input and output paths before using it. Do not move or delete preserved paper data merely to satisfy this check.

It is not necessary to run both this wrapper and the direct CLI command above. Step 3 below assumes the direct CLI output in `postreview_32b_check/`. If you use the wrapper instead, change `--trace` to the wrapper's resulting `tracer/final_output.txt`.

## 2. Evaluate the original 14B Tracer output

```bash
python scripts/evaluate_tracer.py \
  --case 1 --run 1 \
  --task-card "$CHECK_RUN/cards/accepted.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --trace "$CHECK_RUN/critique/tracer/final_output.txt" \
  --model "${EVALUATION_MODEL:-gpt-5.6-luna}" \
  --out tracer_evaluation_check/case1_run01_trace14b.csv
```

This uses the OpenAI API. The saved `accepted.txt` supplies the original analysis requirements, avoiding a mismatch with example cards that may have been edited since the run. `--case` and `--run` are labels written into the CSV; input files are specified explicitly.

After completion, check that the CSV contains a header and requirement-level evaluation rows:

```bash
head -n 5 tracer_evaluation_check/case1_run01_trace14b.csv
```

The evaluator assesses requirement coverage, source references, dependencies, and hallucinations in the Tracer output. It does not assess the physical correctness of the analysis code.

## 3. Evaluate the new 32B Tracer output

Use the Tracer output from Step 1 and the same evaluation model as in Step 2:

```bash
python scripts/evaluate_tracer.py \
  --case 1 --run 1 \
  --task-card "$CHECK_RUN/cards/accepted.txt" \
  --code "$CHECK_RUN/execution/generated_analysis.py" \
  --trace "$CHECK_RUN/postreview_32b_check/tracer/final_output.txt" \
  --model "${EVALUATION_MODEL:-gpt-5.6-luna}" \
  --out tracer_evaluation_check/case1_run01_trace32b.csv
```

```bash
head -n 5 tracer_evaluation_check/case1_run01_trace32b.csv
```

These steps check a review of existing code and an evaluation of each Tracer output. The CSV files contain model-generated judgments and should be reviewed by a person before use.

## If an API request fails

If a request fails with an API error such as HTTP 504, treat that step as incomplete and retry it later. There is no need to delete the existing analysis code or paper data and regenerate the analysis from scratch. Step 2 can be run independently using the existing 14B Tracer output even if Step 1 has not completed.

The batch-evaluation wrappers in `scripts/oldscripts/` are not needed for this single-run check.
