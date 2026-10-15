# LHCO Domain

This package contains the LHCO-specific assets used by the workbench:

- analysis-card parsing;
- the canonical code-generation system prompt;
- construction of the LHCO generation messages;
- helper registry and helper-selection policy;
- LHCO-specific ambiguity guidance for the split Golden Axe Oracle;
- collider-analysis context supplied to the Critique Pipeline.

The code-generation system prompt is preserved as one byte-identical file in
this prototype. Splitting its prose and embedded Python helper implementations
is intentionally deferred so that domain separation does not also change model
behavior.

`[ADDITIONAL_HELPERS]` remains recommendation guidance. It is not treated as an
exhaustive list of functions available to generated code.
