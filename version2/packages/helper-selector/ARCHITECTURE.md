# Architecture and migration notes

## Public component boundary

```text
workflow
   |
   +-- helper_selector (generic package)
   |      +-- prompt construction
   |      +-- output validation
   |      +-- dependency expansion
   |      +-- card revision
   |
   +-- model provider
   |      +-- Hugging Face adapter
   |
   +-- registry integration
          +-- CoLLM/LHCO registry
          +-- domain policy
```

The workflow owns paths and run directories. The selector returns structured
data and does not call CoLLM, the critique pipeline, or the oracle.

## Original-to-public mapping

| Original | Public location |
| --- | --- |
| `helper_selector_hf.py` validation and dependency logic | `src/helper_selector/selection.py` |
| `helper_selector_hf.py` prompt | `src/helper_selector/prompt.py` |
| `helper_selector_hf.py` HF API call | `src/helper_selector/providers/huggingface.py` |
| `helper_registry.py` | `domains/lhco-domain/src/lhco_domain/registry.py` |
| `append_additional_wrappers.py` | `src/helper_selector/cards.py` |
| `run*.sh` | Replaced by CLI; research batch scripts remain outside the public package |
| `analysis_util/` | Excluded from this public component |
| `generated_user_inputs/` | Excluded; these are experiment artifacts |

## Workflow contract

Input:

- immutable task card text;
- a normalized `list[HelperSpec]`;
- a model provider implementing `ChatProvider`.

Output:

- `SelectionResult`;
- raw model response for provenance;
- an optional revised card produced separately from the selection.

Recommended run layout:

```text
runs/<case>/<run-id>/
├── cards/
│   ├── original.txt
│   └── revision_001.txt
└── helpers/
    ├── request.json
    ├── raw_response.txt
    ├── selection.json
    └── summary.txt
```

The original card is never overwritten. Later, the common workflow can pass
`cards/revision_001.txt` to the code-generation backend.
