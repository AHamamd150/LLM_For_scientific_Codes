# Initial shared-layout draft

## Domain-separation prototype

- Renamed the generic backend from `collm-generator` to `code-generator`.
- Added an explicit generation-profile interface.
- Moved LHCO card parsing, canonical system prompt, helper registry, helper
  policy, and Critique context into `domains/lhco-domain`.
- Split model-response handling from Python syntax validation.
- Preserved the canonical LHCO prompt byte-for-byte.
- Preserved one-pass continuation and the workflow-level
  `fix -> regenerate` recovery cycle.
- 49 unit/integration tests pass without model access.

## Oracle domain-context split

- Added `oracle-split`, which combines a generic Golden Axe role prompt with
  domain context supplied by the selected domain package.
- Preserved the previous `oracle` and `oraclet` profiles unchanged.
- Moved Oracle out of `ResearchCodeWorkflow`; it remains a standalone,
  human-reviewed stage.
- Added `scripts/run_oracle.sh`.
- Added a complete non-collider dummy domain and cross-component integration
  test.
  context-leak prevention, and explicit guards against helper-induced
  reinterpretation.
- Added `oracle-split-v3` as the default split profile. It removes the final
  `SUMMARY_REWRITE` and emits per-ambiguity
  `POSSIBLE_CLARIFYING_REWRITES` for both interpretations.

## Included

- Generic Helper Selector with CoLLM registry integration.
- Golden Axe Oracle with `oracle`, `oracle-lite`, and domain-owned `oraclet` profiles.
- Two-stage Critique Pipeline.
- CoLLM LHCO generator backend, continuation handling, executor, and fixer.
- Shared artifact contracts and composed workflow.
- Five original task-card examples and five helper-selected reference cards.
- The original execution recovery cycle: each retry attempts a fix and then,
  if needed, regenerates from the generation card before the next retry.
- `scripts/run_qwen3_14b.sh` to run Helper Selector, generator, fixer,
  tracer, and Critique with one shared Qwen3-14B model setting, followed by a
  post-run Oracle ambiguity review.
- The Hugging Face Oracle provider now disables Qwen3 thinking mode and
  rejects responses that end before a final Oracle answer.
- Final execution products remain directly under `execution/`, while
  attempt, fixer, and regeneration diagnostics are stored under
  `execution/generation_info/`.
- The Qwen3 convenience script now invokes the workflow directly from the
  source tree and no longer requires the `agentic-code-workbench` console
  command to be preinstalled.
- The Qwen3 convenience script no longer runs Oracle as a preflight step that
  automatically continues into generation. Oracle is either a separate
  human-reviewed preflight via `scripts/run_oracle.sh`, or a post-run review
  artifact produced after the main workflow.

## Removed from the shared workflow

- Streamlit GUI.
- MLP, GNN, and Transformer applications.
- model-comparison shell scripts and generated experiment outputs.
- obsolete and failed prompt variants, except where documented.

## Verification

- 49 unit/integration tests pass without network access.
- All Python source compiles.
- The composed Helper Selector → CoLLM → Tracer → Critique workflow and
  standalone Oracle path pass with deterministic mock providers.
- The 69-entry CoLLM helper registry validates successfully.
- CoLLM and Oracle prompts are preserved byte-for-byte. Critique prompts retain
  their rules with the public `Tracer` terminology.

## Remaining optional verification

A small LHCO input file would allow an end-to-end execution/fixer test with a
real generated analysis. Real model calls also require the user's chosen model
access and `HF_TOKEN`; no credentials are stored in this repository.

## Test collection compatibility

- Added a repository-level pytest configuration so `python -m pytest -q` can run the full test suite with the package `src` directories on `PYTHONPATH`.
- Enabled pytest `importlib` import mode for repository-wide collection.
- Renamed duplicate test module basenames to avoid pytest import-name collisions when collecting multiple packages together.
- Added workflow-local pytest configuration so `cd workflows && python -m pytest -q` tests only workflow tests with the required local package paths.

## Workflow domain and input naming cleanup

- Added generic `--input` to the `generate-review` workflow CLI for the
  optional file passed to generated code as `sys.argv[1:]`.
- Added generic `--domain-assets MODULE:OBJECT` so the workflow CLI receives
  the generation profile, helper registry, helper policy, and critique context
  from an injected domain bundle instead of importing `lhco_domain` directly.
- Updated `scripts/run_qwen3_14b.sh` to call the workflow with
  `--domain-assets lhco_domain:DOMAIN` and `--input`, keeping the outer LHCO
  convenience script interface unchanged.
- Renamed the executed generated script artifact from
  `generated_lhco_analysis.py` to `generated_analysis.py`.

## Input/output contract example

- Added `GeneratedScriptIOContract` to `workbench-contracts` as a small typed
  description of how generated scripts receive input and where outputs should
  be written.
- Added `dummy_domain.DUMMY_IO_CONTRACT` and included it in `dummy_domain:DOMAIN`
  as `io_contract`.
- Expanded the dummy domain into a minimal executable example: generated scripts
  read a numbers text file from `sys.argv[1:]`, print a count/sum summary, and
  write `result.txt` in the execution directory.
- The workflow now writes generic `execution/stdout.txt` on successful execution
  while preserving `execution/cutflow.txt` as the LHCO-compatible alias.
