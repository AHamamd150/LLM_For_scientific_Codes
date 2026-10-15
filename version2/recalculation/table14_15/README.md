# Table 14–15: E6 boundary-tracing reaggregation

## Source data

`paper_data/tracer_evaluation/E6_run_level_current.csv` is the **unchanged** run-level classification provided for the revision. It has 130 unique `(model, case, run, condition_id)` records: 90 for 14B and 40 for 32B. The CSV records the classified tracer statement together with cited code/tracer evidence and source-bundle references. Those original source paths refer to the collection/bundle at the time of annotation; they have not been rewritten to follow `paper_data/runs/` relocations.

This is a *recount of existing judgments*, **not** an independent source-code audit of every E6 classification.

## Recompute

From the `test_runs` repository root:

```bash
python3 recalculation/table14_15/recompute_table14_15.py
```

The script reads the existing CSV without modification, checks duplicate keys and class consistency, makes no API/LLM calls, and writes only:

- `recalculation/table14_15/results/table14_recomputed.csv`
- `recalculation/table14_15/results/table15_recomputed.csv`

## Counting conventions

- **Table 14**: `include_in_global_14B_E6_table == yes` (90 records). 70 two-sided windows + 20 MET lower-bound entries.
- **Table 15**: `include_in_case_model_E6_comparison == yes` (110 records). Only two-sided boundaries: 70 from 14B Cases 1–5, 20 from 32B Case 2, 20 from 32B Case 6.
- `complete` → Pass; `partial_condition_only` → Partial; `partial_quantity_only` → Fail; `na` → N/A.
- Recovery = `(Pass + Partial)/(Items − N/A)`; **Pass** alone measures complete semantic capture. `Fail` here means the tracer did not reconstruct the complete boundary (it is not automatically a code-generation failure).

## PDF reconciliation

- Table 14 agrees with the current manuscript (49 complete, 25 condition-only, 15 quantity-only, 1 N/A).
- Table 15: **Case 5 / 14B N/A must be 0, not 10**; **14B Total N/A must be 1, not 11**. The corresponding evaluated denominators (10 and 69), rates, and other class counts remain unchanged.
- The single genuine N/A is 14B Case 2 Run 07 (`c2_mtop_100_250`), where the boundary was absent from generated code.
- Table 15 class names differ from Table 14: Table 14's `Partial: quantity only` is labeled `Fail` in Table 15, because the cut boundary itself was not recovered.

## Original scratch extracts

`bounded_cuts.txt`, `lower_only_cuts.txt` and `continue_list` were intermediate extracts, not source annotations for this recount. They are not used by the script. Before deleting, confirm the copies you are removing are these scratch extracts rather than experiment or evaluation outputs.
