# Architecture

## Dependency direction

```text
golden-axe-oracle <── domain oracle_context
        |
        v
human clarification / accepted card

workflows
├── code-generator
├── lhco-domain ──> helper-selector
├── critique-pipeline
└── workbench-contracts
```

No reusable component imports the workflow. Generic components do not import
`lhco-domain`; the workflow supplies the concrete profile, registry, policies,
and critique context. Golden Axe runs before the workflow and accepts domain
context independently.

## Responsibilities

- `golden-axe-oracle`: produce a free-form preflight ambiguity report.
- `helper-selector`: select exact helper names and expand dependencies.
- `code-generator`: generate and validate Python source using an injected
  generation profile.
- `lhco-domain`: provide LHCO card interpretation, prompts, helper metadata,
  and domain policies.
- `critique-pipeline`: extract implemented behavior and compare it with the card.
- `workflows`: own post-acceptance artifact paths and compose helper selection,
  generation, execution recovery, and critique.

## Preserved experimental behavior

- The canonical CoLLM system prompt is copied byte-for-byte.
- The canonical Oracle and small-model OracleT prompts are copied byte-for-byte.
- The Critique Pipeline prompts preserve the supplied rules; public terminology
  is changed from `EXPLAIN OUTPUT` to `TRACER OUTPUT`.
- Helper dependency expansion reproduces the supplied 14B selection example.
- Critique continuation, repair, definition parsing, and finding filtering are
  retained.

## Deliberate changes

- Importing the generator no longer installs packages automatically.
- Python registry files are imported as modules instead of executed as text.
- Model/API calls are behind provider interfaces.
- Input cards are never overwritten.
- GUI and deep-learning applications are excluded.
- A truncated block ending in `:` receives indentation-safe continuation
  merging.
