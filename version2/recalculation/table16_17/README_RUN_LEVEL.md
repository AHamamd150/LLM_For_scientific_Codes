# Tables 16 and 17 — run-level adjudication addendum

This addendum **does not replace or modify** the existing aggregate summary CSV or `recompute_table16_17.py`. Install into the existing `test_runs` repository alongside them.

```bash
python3 recalculation/table16_17/recompute_table16_17_from_runs.py
```

Inputs:
- `paper_data/tracer_evaluation/critique_summary/case2_6_case5_7_run_level_adjudication.csv` (new; preserved 210-row issue/run adjudication file)
- `paper_data/tracer_evaluation/critique_summary/case2_6_case5_7_critique_summary.csv` (existing 16-row aggregate)

The script checks 21 unique issue/setting groups (ten runs per group), validates missing/not-applicable adjudications and recovers **all 13 published Table 16–17 rows**. Results are written to new `results/*_from_runs.csv` files so existing results remain untouched. Three supplemental summary cases and all 21 groups have separate output files.

## Important provenance limitations

- For **Case 6 / 14B, muon eta mismatch**, generation 10/10 and tracer 10/10 are recoverable from the new run-level CSV, but the per-run Critique detection outcome is `unresolved_run_mapping` in **all ten rows**. The published **Critique 9/10** is retained only from the previous aggregate summary, marked `summary-only` in output. It is not independently recovered from run-level annotations. To recover the exact run IDs, consult the original Critique responses.
- The supplemental **Case 5 / 32B, cutflow** row had no fixed strict critique count in the earlier summary, although the new run-level sheet marks five missed. We preserve the summary's unknown status in `supplemental_from_runs.csv` and do not introduce a new published number.
- These are reproductions of **existing adjudications**, not independent re-analyses of the generated code or Tracer/Critique source outputs.

Do not publish a claim that the 9/10 Critique value has been independently recomputed from run-level evidence until the missing run mapping is verified.
