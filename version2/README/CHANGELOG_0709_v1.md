# agentic-code-workbench 0709_v1

This update is intentionally limited to the helper-selector prompt split.

## Changed

- Updated the generic helper-selector system prompt to use the package term
  `spec` consistently.
- Kept domain-independent closed-list selection rules in the generic helper
  selector prompt:
  - exact registry names only;
  - no invented, renamed, shortened, generalized, or aliased helper names;
  - select only helpers justified by explicit spec requirements;
  - define `rejected_but_close`;
  - JSON-only output.
- Moved LHCO/physics-specific helper-selection rules into the LHCO domain
  helper policy:
  - cuts, vetoes, reconstruction steps, plotted quantities, histograms,
    requested observables, and requested output quantities should be accounted
    for;
  - domain-specific helpers require explicit physics object, decay channel,
    reconstruction target, or observable support in the spec;
  - avoid selecting helpers from other physics channels or reconstruction
    targets merely because they involve similar particles, masses, or kinematic
    variables;
  - respect selected-object workflows for downstream quantities.

## Not changed in this version

- `default_helpers=("read_lhco",)` has not yet been moved to the LHCO domain
  assets. This is planned for a later update.
- I/O contract handling has not been changed. The current convention remains
  that generated scripts run in the execution directory and may write relative
  output paths there, while stdout is captured by the workbench.
