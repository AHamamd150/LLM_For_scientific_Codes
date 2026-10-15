# Table 12 recount — Version 2 (14B, Cases 1–5)

The present recount is a **new adjudication ledger**, not a modification of the GPT-5.6-Luna primary annotations or historical pre-adjudication CSVs. The existing `caseN_14B_runs01_10_review.csv` documents the source inspection; `review/table12_adjudication_addendum.csv` records selected decisions confirmed in the current review discussion.

## Run

From the root of `test_runs` (Version 2):

```bash
python3 recalculation/table12/recompute_table12.py
```

The script reads the **50 archived primary CSVs** under `paper_data/tracer_evaluation/14B/`, validates the requirement totals, and aggregates the explicitly recorded decisions. It writes `results/table12_recomputed.csv` and `results/table12_counted_items.csv` without changing inputs or running any LLM.

The table is not an assertion that **all 1303 items** were individually adjudicated by a human. Selected high-priority findings were examined against generated programs and tracer outputs; other rows retain model-assisted screening (with E1–E5 exceptions). The row-level addendum describes the accepted issue patterns.

## Policy decisions / why counts changed

1. **Case 1:** Accept strict-versus-inclusive MET 30 GeV boundary shorthand in eight traces as operationally immaterial, with exact cut-control semantics covered separately by E6.
2. **Case 2:** Count a reference to `helper_invariant_mass(...)` as a **hallucinated implementation provenance** if the corresponding loop actually uses composite object's `['mass']` field. The numerical equivalence of the quantity does not justify claiming a helper call that was not made. This adds seven hallucination items (Run 01: R9/R16/R17; Run 09: R9/R15/R16; Run 10: R9). Run 07 R16 is the independent fabricated `top_mass_list.append(top_mass)` item. Run 01 R18 omits the semantically defining `min_dr` reduction and counts as one dependency error. Run 10 R12–R21 are ten genuine plot-coverage misses, regardless of mentions of some quantities in Definition Summary.
3. **Case 3:** Run 09 R9 cites non-existent source lines; count one source error, not an additional extra-claim error.
4. **Case 4:** No substantive tracer fidelity error was identified under E1–E5.
5. **Case 5:** R5 and R8 invent named `ditau_obj` and `dijet_obj` in every run (20 hallucinations). R13 is accepted under E1/E2 because `n_bjets(event, pt_cut=30, eta_cut=4.7)` correctly reproduces the veto and the tracer's shorthand does not change the understood selection. The old ten dependency errors are **not carried over** under the newly documented policy. There is no separate retained dependency item in the audited review. This is a new recounted classification, not a reconstruction of the missing historical decision ledger.

For overlapping primary labels on one unsupported operation, this recount uses one substantive issue classification rather than automatically double-counting its source/dependency/hallucination flags. Identical additional claims (`EXTRA`) are not counted a second time.

## Important limitation

The recount is derived from **explicit issue decisions plus archived primary requirement totals**, not a new line-by-line human review of all 1303 items. If an unreviewed problem is discovered later, add a row to the addendum and regenerate the table. No existing Luna annotation or historical reviewer file needs to be edited.

The main text's assessment-method paragraph should specify that **only selected high-priority issues received researcher confirmation**, rather than stating that all annotations were human-adjudicated.
