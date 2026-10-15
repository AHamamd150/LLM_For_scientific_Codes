# Architecture and migration notes

## Component boundary

```text
task card ─┐
registry ──┼─> Golden Axe prompt ─> model provider ─> raw report
codegen ───┘
 prompt
```

The registry and code-generation prompt are context, not hard dependencies.
Golden Axe neither selects helpers nor invokes code generation.

The release `oracle` profile is assembled from three conceptual layers:

```text
generic Golden Axe front matter + domain prompt/context + output contract
```

The selected profile decides the default output-contract source.  `oracle` uses
the shared system output contract.  `oraclet` uses the same generic front matter
but expects the selected domain to provide category definitions and output rules
through `--oracle-context`.

The workflow owns the run directory and any later interaction with the user:

```text
runs/<case>/<run-id>/
├── cards/
│   ├── original.txt
│   └── revision_001.txt
└── oracle/
    ├── request.json
    ├── user_message.txt
    └── response_001.txt
```

Golden Axe only writes under `oracle/`. It never overwrites the input card.

## Original-to-public mapping

| Original | Public location |
| --- | --- |
| `run_golden_axe.py` prompt assembly | `src/golden_axe/prompt.py` |
| `run_golden_axe.py` HF call | `src/golden_axe/providers/huggingface.py` |
| `golden_axe_system_prompt_oraclet.txt` | `domains/<domain>-domain/src/<domain>_domain/prompts/oraclet_domain_prompt.txt` after removing duplicated generic front matter |
| `run_*.sh` | Replaced by the CLI; research batch scripts stay outside |
| `outputs*/` | Excluded as experiment artifacts |
| `old/` and `previous_stable*.txt` | Excluded from the public component |

`oracle` is the canonical default and is the release name for the former `oracle-split-v3` prompt.
It treats the report as a
human clarification artifact and uses per-ambiguity
`POSSIBLE_CLARIFYING_REWRITES` instead of a final `SUMMARY_REWRITE`.
`oraclet` remains supported as a domain-owned output profile.  Its
LHCO-specific wording is stored in the LHCO domain package rather than in the
generic system package.  `oracle-lite` is exposed as the legacy pre-package
monolithic prompt.  `oraclet-grounded` was an unsuccessful prompt design and is
not exposed.

There is deliberately no response parser. Existing outputs demonstrate that
models can reorder sections or vary headings despite prompt instructions.
Preserving the complete raw report avoids inventing unreliable structure.
