# Critique Pipeline

The pipeline performs semantic review of generated code in two stages:

1. `tracer`: derive an AS-IMPLEMENTED SPEC and trace concrete definitions.
2. `critique`: compare that trace with the original task card and report
   semantic mismatches, ambiguities, missing behavior, and extra behavior.

The package does not generate or execute code. A workflow passes it an immutable
task card and the generated source file.

## Install

```bash
python -m pip install -e ".[huggingface]"
```

## Run

```bash
export HF_TOKEN=...

critique-pipeline run \
  --card cases/case_001/card.txt \
  --code runs/case_001/generation/src/analysis.py \
  --domain-context ../../domains/lhco-domain/src/lhco_domain/prompts/critique_context.txt \
  --tracer-model Qwen/Qwen3-14B \
  --critique-model Qwen/Qwen3-14B \
  --n-runs 1 \
  --run-dir runs/case_001/critique
```

`--domain-context` is optional. The generic package contains no built-in
collider or LHCO context; callers inject the relevant domain text.

Output:

```text
runs/case_001/critique/
├── request.json
├── tracer/
│   ├── final_output.txt
│   ├── collections.json
│   └── round_*_raw_response.json
└── critique/
    ├── response_001.txt
    ├── raw_001_call_01.json
    └── filtered_review.txt
```

The raw critique remains available even when a finding is removed from the
heuristically filtered review.
