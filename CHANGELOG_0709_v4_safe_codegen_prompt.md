# 0709 v4 safe codegen prompt update

This update builds on `agentic-code-workbench_0709_v4_safe_registry`.

## Changes

- Preserved the previous LHCO code-generation prompt as:
  - `domains/lhco-domain/src/lhco_domain/prompts/codegen_system_legacy.txt`
- Replaced `codegen_system.txt` with a selected-object-safe prompt variant.
- Removed legacy event-level and analysis-level convenience helper definitions from the active codegen prompt, including:
  - `compute_ht(event)`
  - `dijet_mass(event)`
  - `mt_lepton_met(event)`
  - `helper_delta_phi_l_twojet(event)`
  - event-level dilepton/dijet/diphoton/ditau mass wrappers
  - Z/W/Higgs/tau candidate-finder wrappers such as `find_z_candidate(...)` and `find_w_candidate_leptonic(...)`
- Extended the safe registry exclusion list to also hide analysis-level candidate-finder helpers.

## Rationale

Safe registry filtering alone was not sufficient, because the generator could still use legacy helper definitions embedded in the LHCO codegen system prompt.  This update tests whether generation can proceed using only lower-level selected-object-safe helper composition.

Preferred patterns are now:

- `sum_objects(selected_obj1, selected_obj2)`
- `helper_invariant_mass(selected_obj1, selected_obj2)`
- `helper_transverse_mass(selected_lepton, met)`
- `helper_delta_phi(obj1["phi"], obj2["phi"])`
- `helper_delta_r(obj1, obj2)`
- `scalar_pt_sum(selected_jets)`
