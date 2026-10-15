# Agentic Code Workbench

A modular workflow for preflight clarification, helper selection, code
generation, and semantic review.

The code generator is profile-driven. LHCO-specific prompts, card parsing, and
helper metadata are supplied by a separate domain package. The Oracle, Helper
Selector, Code Generator, and Critique Pipeline remain reusable components.

## Repository layout

```text
agentic-code-workbench/
├── packages/
│   ├── workbench-contracts/
│   ├── helper-selector/
│   ├── golden-axe-oracle/
│   └── critique-pipeline/
├── backends/
│   └── code-generator/
├── domains/
│   ├── lhco-domain/
│   └── dummy-domain/        # domain-swap test fixture
├── workflows/
├── examples/
│   ├── cases/
│   └── reference/helper-selected/
└── tests/
```

## Workflow

```text
cases/<case>/card.txt
        |
        v
Golden Axe Oracle
        |
        v
human clarification / accepted card
        |
        v
Helper Selector <---- LHCO helper registry
        |
        v
generation card with [ADDITIONAL_HELPERS]
        |
        v
Code Generator + LHCO profile
        |
        v
generated Python source
        |
        +---- optional execution and error-driven fix
        |
        v
Critique Pipeline: tracer -> critique
```

The Oracle-to-accepted-card transition is intentionally a human decision. The
Oracle report is never applied automatically.

## Run artifacts

```text
runs/<case>/<run-id>/
├── cards/
│   ├── original.txt
│   ├── accepted.txt
│   └── generation.txt
├── oracle/
│   ├── request.json
│   └── response_001.txt
├── helpers/
│   ├── selection.json
│   ├── summary.txt
│   └── raw_response.txt
├── generation/
│   ├── result.json
│   ├── response_001.txt
│   └── src/analysis.py
├── execution/
│   ├── generated_analysis.py
│   ├── stdout.txt
│   ├── cutflow.txt  # LHCO-compatible stdout alias
│   ├── *.png / *.csv
│   └── generation_info/
│       ├── attempt_001_initial_*
│       ├── attempt_002_fix_*
│       └── attempt_003_regen_*
└── critique/
    ├── tracer/
    └── findings/
```

Input cards under `examples/cases/` are immutable examples. Revised cards and
all model outputs belong under `runs/`.

Execution is optional. If no LHCO test file is supplied, the generated source
is reviewed directly by the Critique Pipeline.

## Installation

Each component is an independent Python package. For a development installation:

```bash
python -m pip install -e packages/workbench-contracts
python -m pip install -e packages/helper-selector
python -m pip install -e packages/golden-axe-oracle
python -m pip install -e packages/critique-pipeline
python -m pip install -e backends/code-generator
python -m pip install -e domains/lhco-domain
python -m pip install -e workflows
```

Install the relevant optional provider dependency, for example:

```bash
python -m pip install -e "backends/code-generator[huggingface]"
python -m pip install -e "workflows[huggingface]"
```

## Commands

Run Oracle preflight first. Oracle is a standalone human-in-the-loop stage:

```bash
./scripts/run_oracle.sh \
  examples/cases/user_input_5.txt \
  runs/case_5/run_001/oracle
```

The script uses the release `oracle` profile by default.  The generic Golden
Axe front matter comes from `golden-axe-oracle`, while LHCO ambiguity guidance
comes from `lhco-domain`.  The backward-compatible name `oracle-split-v3`
remains available as an alias for `oracle`.

`PROFILE=oraclet` uses a domain-complete OracleT prompt from
LHCO-specific categories and output format from the domain prompt
`domains/lhco-domain/src/lhco_domain/prompts/oraclet_domain_prompt.txt`.

After reviewing the Oracle report, pass the accepted or manually revised card
to the remaining workflow:

```bash
agentic-code-workbench generate-review \
  --card runs/case_5/run_001/cards/accepted.txt \
  --domain-assets lhco_domain:DOMAIN \
  --helper-model Qwen/Qwen3-14B \
  --generator-model Qwen/Qwen2.5-Coder-14B-Instruct \
  --tracer-model Qwen/Qwen3-14B \
  --critique-model Qwen/Qwen3-14B \
  --run-dir runs/case_5/run_001
```

Add `--input sample.lhco --max-retries 2` to execute the generated code
before Critique. Each retry first attempts an error-driven fix and, if that
still fails, regenerates the code from the accepted generation card.
`--fixer-model <model>` may select a separate fixer model; otherwise the
generator model is reused.

### Re-run the main workflow with Qwen3-14B

The convenience script below uses `Qwen/Qwen3-14B` for Helper Selector,
generator, fixer, tracer, and Critique. It runs the Oracle only after the main
workflow, as a saved ambiguity review for the next iteration:

```bash
export HF_TOKEN="your-token"

./scripts/run_qwen3_14b.sh \
  examples/cases/user_input_5.txt \
  /path/to/small-test.lhco \
  runs/qwen3_14b/case_5
```

The script takes exactly three arguments:

```bash
./scripts/run_qwen3_14b.sh CARD LHCO_FILE RUN_DIR
```

The usual settings can be changed without editing Python source:

```bash
MODEL="Qwen/Qwen3-14B" MAX_RETRIES=2 \
  ./scripts/run_qwen3_14b.sh CARD LHCO_FILE RUN_DIR
```

The post-run Oracle profile defaults to `oracle` and can be changed
with `ORACLE_PROFILE=<profile>`.

The script currently uses the Hugging Face API providers. A local
Transformers model runner is not included in the shared package.
The script sets the repository package paths itself, so editable installation
is not required when it is run from an extracted source tree.

For a human-in-the-loop preflight workflow, run `scripts/run_oracle.sh` first,
review the Oracle output, manually revise the card, and then pass that revised
card as the first argument to `run_qwen3_14b.sh`.

## Scope of the code-generation extraction

The generic backend includes continuation handling, model-response processing,
Python validation, execution, and error-driven fixing. The canonical LHCO
system prompt and helper metadata live in `domains/lhco-domain`.

The former Streamlit GUI and MLP/GNN/Transformer applications are not included.
They are unrelated to the modular code-generation workflow and remain
recoverable from the original source archive.

## Verification

All component tests can be run without model downloads or API access:

```bash
./scripts/test_all.sh
```
