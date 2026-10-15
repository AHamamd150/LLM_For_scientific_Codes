# Code generator / LHCO domain separation prototype

## Resulting boundary

```text
backends/code-generator/
└── src/code_generator/
    ├── generator.py
    ├── model_response.py
    ├── python_validation.py
    ├── fixer.py
    ├── executor.py
    └── providers/

domains/lhco-domain/
└── src/lhco_domain/
    ├── profile.py
    ├── cards.py
    ├── registry.py
    └── prompts/
        ├── codegen_system.txt
        ├── helper_policy.txt
        ├── oracle_context.txt
        └── critique_context.txt
```

`CodeGenerator` depends only on a small `GenerationProfile` protocol:

```python
class GenerationProfile(Protocol):
    response_rejection_markers: tuple[str, ...]

    def build_messages(self, card_text: str) -> list[dict[str, str]]:
        ...
```

The marker tuple lets a profile reject an echoed domain card from the raw-code
fallback without putting domain section names into `model_response.py`.

The workflow constructs the generic generator with the concrete profile:

```python
generator = CodeGenerator(provider, LHCO_PROFILE)
```

## Preserved behavior

- The LHCO code-generation prompt is byte-for-byte unchanged.
- The canonical `oracle` and `oraclet` prompts remain available unchanged.
- One continuation response is allowed per generation.
- Model-response cleanup, code extraction, incomplete detection, and
  overlap-aware continuation merge retain their previous implementation.
- Execution recovery remains in the workflow.
- Every retry still performs `fix -> execute -> regenerate -> execute`.
- `[ADDITIONAL_HELPERS]` remains a recommendation list, not an exhaustive
  dependency declaration.
- Final execution products and `execution/generation_info/` retain the portable
  runner layout.

## Deliberate API changes

- Distribution `collm-generator` is renamed to `code-generator`.
- Python package `collm_generator` is renamed to `code_generator`.
- `CoLLMGenerator` is renamed to `CodeGenerator`.
- `CodeGenerator` now requires an explicit generation profile.
- Distribution `collm-helper-registry` is replaced by `lhco-domain`.
- Python package `collm_registry` is replaced by `lhco_domain`.
- Critique domain context is injected by the caller instead of being embedded
  in the generic Critique Pipeline package.
- `oracle` separates the generic Golden Axe role and output contract from
  LHCO-specific ambiguity guidance.
- Oracle is run as a standalone human-in-the-loop stage rather than as a method
  of `ResearchCodeWorkflow`.

## Domain-swap verification

`domains/dummy-domain` supplies a non-collider generation profile, helper
registry, helper policy, Oracle context, and Critique context. An integration
test runs those assets through the generic components to guard against hidden
LHCO imports.

## Deferred work

The large `codegen_system.txt` still contains both model instructions and
embedded Python parser/helper implementations. They can later be separated
into maintained source fragments and reassembled deterministically, but that
should be a distinct change with prompt-equivalence tests.
