# Tables 16 and 17: verified run-level recount

This package **adds** a verified source CSV and a new aggregation script. It does not replace the original per-run adjudication CSV, the 16-row aggregate summary, the earlier scripts, or any existing results.

From the `test_runs` repository root, run:

```bash
python3 recalculation/table16_17/recompute_table16_17_verified.py
```

## Source

`paper_data/tracer_evaluation/critique_summary/case2_6_case5_7_run_level_adjudication_verified.csv`

- 210 adjudication rows: 21 `(setting, issue_id)` groups with runs 1–10 each.
- Contains `generation_error`, `tracer_exposed`, `critique_outcome`, `critique_detected_strict` and `critique_partial` for each run.
- The corrected Case 6 / 14B muon-eta issue identifies **Run 04** as the sole strict Critique miss; 9/10 detections are now directly countable from these rows.
- The additional Case 5 / 32B cutflow issue has five affected runs (04, 06, 07, 09, 10), 0/5 Tracer exposure and 0/5 Critique detection **according to the recorded run-level adjudications**. This supplemental issue is **not included** in Tables 16 or 17. The older summary left its Critique count unspecified.

## Output files (all new filenames)

- `results/table16_verified_from_runs.csv`: ten Table 16 rows
- `results/table17_verified_from_runs.csv`: three Table 17 rows
- `results/supplemental_verified_from_runs.csv`: three auxiliary rows, not reported in either table
- `results/all_21_groups_verified_from_runs.csv`: every group, with counted runs and explicit run IDs

`Generation error` reports affected runs out of ten. `Tracer exposure` and `Critique detection` are conditioned on the run containing the indicated generation error, hence the denominator is the number of affected runs. `N/A` indicates no generation errors for that issue/setting. The special “correct + partial” entry retains the distinction in the existing Table 16.

## Scope and provenance

The script uses **only the verified run-level CSV**. It does not require `case2_6_case5_7_critique_summary.csv`, any network access, or LLM reruns. It checks completeness, run IDs, duplicated rows, label consistency, and the resolved Run 04 mapping.

These figures reproduce the **archived adjudications**; running the script is not an independent re-audit of original generated code or Tracer/Critique responses. The published Table 16 and Table 17 values remain unchanged.
