# Golden Axe Oracle

Golden Axe is a preflight critic. It reads a task card and optional contextual
material, then returns a free-form clarification report before helper selection
or code generation.

It does not modify the card automatically and does not parse its own answer
into a pass/fail decision. The raw response is the authoritative output.

## Install

```bash
python -m pip install -e ".[huggingface]"
```

## Run

```bash
export HF_TOKEN=...

golden-axe run \
  --card cases/case_001/card.txt \
  --registry-module lhco_domain.registry:HELPER_REGISTRY \
  --profile oracle \
  --oracle-context ../../domains/lhco-domain/src/lhco_domain/prompts/oracle_context.txt \
  --oracle-output-contract auto \
  --model Qwen/Qwen2.5-14B-Instruct \
  --run-dir runs/case_001/oracle
```

Bundled profiles:

- `oracle`: the default release profile.  It is the former
  `oracle-split-v3` prompt rendered from a system front section, domain context,
  and the shared system output contract.
- `oracle-split-v3`: backward-compatible alias for `oracle`.
- `oracle-lite`: the pre-package monolithic Golden Axe prompt kept for
  compatibility and comparison.  "Lite" here means legacy single-file prompt,
  not a smaller or weaker model profile.
- `oraclet`: OracleT rendering mode.  The system package supplies only generic
  front matter; the selected domain must supply the OracleT category and output
  rules via `--oracle-context`.

The default profile is `oracle`. A local prompt can instead be supplied with
`--system-prompt`.

## Output-contract mode

Split prompts are rendered from three conceptual layers:

```text
system front matter
DOMAIN_CONTEXT / domain middle
output contract
```

Use `--oracle-output-contract` to choose how the output rules are supplied:

- `auto`: use the selected profile default.
- `system`: append the shared system output contract.
- `domain`: do not append the shared system output contract; the domain prompt
  is expected to define its own output rules.
- `none`: do not append any output contract.

The normal defaults are:

```text
oracle      -> system
oracle-lite -> domain-owned monolithic prompt
oraclet     -> domain-owned domain prompt via --oracle-context
```

The command writes:

```text
runs/case_001/oracle/
├── request.json
├── user_message.txt
└── response_001.txt
```

With `--runs N`, one response file is written for each independent run. The
workflow can present these reports to the user and place an accepted revised
card under `runs/<case>/<run-id>/cards/`.

For LHCO OracleT, pass the domain prompt explicitly, for example:

```bash
golden-axe run \
  --card cases/case_001/card.txt \
  --registry-module lhco_domain.registry:HELPER_REGISTRY \
  --profile oraclet \
  --oracle-context ../../domains/lhco-domain/src/lhco_domain/prompts/oraclet_domain_prompt.txt \
  --oracle-output-contract auto \
  --model Qwen/Qwen2.5-14B-Instruct \
  --run-dir runs/case_001/oraclet
```
