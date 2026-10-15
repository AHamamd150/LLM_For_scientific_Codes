# Table 12: High-priority triage for 14B tracer assessment

This is **provisional screening**, not expert adjudication and not Table 12 recomputation.
No API calls, generation, or tracer reruns are performed, and no files under `paper_data/` are modified.

From the `test_runs` root:

```bash
python3 recalculation/table12/screen_high_priority.py
```

Input: exactly 50 original pre-annotation CSVs from `paper_data/tracer_evaluation/14B/`.
The script verifies that each Case 1–5 has Run 01–10 and that 1303 requirement rows are present. Extra claims are counted **separately** from requirements.

The ZIP includes the existing reference worksheet at `recalculation/table12/review/14B_reference_six_review.csv` (copied verbatim from the previously prepared review checklist). It provides priorities for the previously inspected six runs. **Those priorities are not records of completed human checks.** They should not be confused with `expert_final` decisions, which were blank in the original pre-adjudication files. All other runs are sorted conservatively:

- **High / 要確認:** `hallucination=yes`, `source_correct=no`, `dependency_correct=no`, or `traced=no` in the original Luna annotation. These are *potential* issues; E1–E5 may allow some of them.
- **Medium / 参考確認:** only partial traces or `uncertain` judgments, without a stronger adverse flag.
- **Low / 通常:** no adverse flag. This **does not mean independently confirmed correct**.

The script **does not automatically apply E1–E5 to the remaining 44 runs**: deciding equivalence, acceptable plot provenance, or task–code mismatch requires semantic inspection. High is therefore a *candidate review queue* rather than the final small subset for expert adjudication. A subsequent model-assisted E1–E5 re-screen, with code evidence and transparent uncertainty, may reduce it further before expert review.

Outputs are placed in `recalculation/table12/results/`:

- `all_14B_screening.csv`: all original assessment rows plus screening fields
- `high_priority_review.csv`: only High rows, with code/tracer paths and blank expert decision fields
- `summary_by_case.csv`: counts by case (including affected runs)
- `summary.json`: totals, reference-worksheet usage, and method

Use `high_priority_review.csv` to inspect the generated code and tracer report. Keep the source CSVs and adjudication records unchanged. Do not interpret `extra_trace_claim` rows as extra task-card requirements or count duplicates as independent semantic issues.
