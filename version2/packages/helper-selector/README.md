# Helper Selector

`helper-selector` selects names from a closed helper registry and expands their
declared dependencies. It does not import CoLLM and does not generate code.

The package is intended to live at:

```text
packages/helper-selector/
```

CoLLM/LHCO-specific registry data belongs outside the package:

```text
domains/lhco-domain/
```

## Install

```bash
python -m pip install -e ".[huggingface]"
python -m pip install -e ../../domains/lhco-domain
```

## Run

```bash
export HF_TOKEN=...

helper-selector select \
  --spec path/to/card.txt \
  --registry-module lhco_domain.registry:HELPER_REGISTRY \
  --policy ../../domains/lhco-domain/src/lhco_domain/prompts/helper_policy.txt \
  --model Qwen/Qwen3-8B \
  --run-dir runs/case_001/helpers
```

This writes:

```text
runs/case_001/helpers/
├── request.json
├── raw_response.txt
├── selection.json
└── summary.txt
```

To create a revised card without overwriting the original:

```bash
helper-selector update-card \
  --card cases/case_001/card.txt \
  --selection runs/case_001/helpers/selection.json \
  --output runs/case_001/cards/revision_001.txt
```

The workflow layer should call `select_helpers()` and
`update_card_with_helpers()` directly. The CLI is primarily for standalone use
and reproducible tests.

Run the dependency-free unit tests with:

```bash
python -m unittest discover -s tests
```
