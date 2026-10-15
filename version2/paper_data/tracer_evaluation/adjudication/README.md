# Tracer pre-adjudication records (Version 2)

These records preserve the LLM-assisted **pre-adjudication** using expert rules E1–E5. They are **not** independently confirmed expert-final annotations.

- `EXPERT_ADJUDICATION_RULES.md`: E1–E5 rules as originally provided.
- `14B/reference_six_runs/`: Six diagnostic samples (Case 1 run 01; Case 2 runs 01 and 07; Case 3, 4, and 5 run 01). `all_six_pre_adjudication.csv` concatenates the six individually preserved files and has 156 `requirement` rows and 5 `extra_trace_claim` rows. The `expert_final` column is blank throughout.
- `32B/`: All 10 runs of Case 2 and all 10 runs of Case 6. Each file uses `pre_adjudication_result` (`no_issue`, `accept_under_rule`, `retain_issue`) and contains no separately confirmed expert-final labels.

## Data integrity check (upon packaging)

- The 14B combined CSV exactly agrees with each of the six individual CSVs after removing the added `sample` column.
- 32B Case 2: 224 requirement rows, 12 extra claims, 4 `retain_issue` rows (4 runs).
- 32B Case 6: 250 requirement rows, 11 extra claims, 2 `retain_issue` rows (2 runs).
- No duplicate `(sample, req_id, row_type)` keys in the combined 14B CSV, or duplicate `(run, req_id, row_type)` keys in the 32B files.
- See `MANIFEST.sha256` for SHA-256 digests of the archived source files.

## Relationship to Appendix tables

- Appendix Table 12 uses **all 50 runs of the 14B tracer evaluation**, not just these six diagnostic runs. This archive alone is insufficient to recompute Table 12.
- The 32B records provide candidate adjudications for other tracer comparisons, not Table 12's 14B totals.
- E6 boundary/control-flow evaluations are separate and not contained in these records.

## Next verification step

Review candidate genuine errors against the original `generated_analysis.py`, the tracer's `final_output.txt`, and the relevant task card. Preserve the original model-generated annotation and record any independent expert decisions in a *separate* CSV; never overwrite these pre-adjudication records. This archived data set is read-only provenance.
