# Table 12 review — Case 4, Qwen3-14B, runs 01–10

## Scope and audit boundary

- Inputs: 10 original `generated_analysis.py`, 10 Tracer `final_output.txt`, and 10 GPT-5.6-Luna screening CSV files, supplied in `case4_14b_review.zip`.
- This is **a new model-assisted source-code review**. Original evaluation CSVs are not modified.
- The `expert_confirmation` and `expert_note` fields remain blank until the researcher accepts or revises the findings.
- Review is about **whether the Tracer reports the code faithfully**, not whether the generated code meets every task-card requirement.

## Structural counts

- 10 run records, **238 screening requirements** in total (the counts vary because the preliminary evaluator grouped some requirements differently).
- **3 distinct generated programs** (runs 01,03,04,05,06,07,09,10 share one program; run 02 and run 08 have different programs).
- **7 distinct Tracer text outputs** (runs 03,06,07,10 have identical Tracer output).
- None of the 238 screening rows has `hallucination=yes`.
- Primary negative source/dependency flags occur predominantly where the Trace identifies observable data and provenance but omits explicit `plt.hist` calls; this is allowed by E3.

## Review outcome (provisional until expert confirmation)

No substantive Tracer hallucination, wrong collection or composite dependency, or source-reference error requiring inclusion in Table 12 was confirmed across the 10 runs.

| Screened pattern | Decision | Reason |
| --- | --- | --- |
| Plot-specific source/dependency marked `no` or `partial` | Accept (E3) | The required scientific observable and its data/provenance are identified; explicit plot call, bins, labels or file name are not mandatory. |
| Cutflow printing, counter order and skip/continue placement | Accept (E4) | Relevant cut and `cutflow` information is included; bookkeeping granularity is not enforced in the primary E1–E5 measure. |
| Rejection conditions represented as logical predicates | Accept (E1) | Computed effective selections are properly identified. |
| Run 07: preliminary evaluator produced only 14 grouped requirements | **Not a Tracer coverage miss** | The Tracer text enumerates all ten scientific plots even though the evaluator groups them in one CSV row. Different from Case 2 / Run 10 where the Tracer itself omits the plot list. |
| Runs 02 and 08: Z-mass plot omits the requested 60–120 GeV range in the generated script | Code-generation discrepancy, not Tracer error (E5) | The Tracer identifies `z_masses` / `z_mass_list` correctly. The quoted 60–120 range is from the task-card requirement; the Tracer does not substantively claim that `plt.hist` implements this range. |

## Direct source checks

- **Run 01 (representative common implementation):** `z_obj = sum_objects(e1, e2)` at line 265; Z-mass validation list at line 294; mass plotting call at line 315; plot data provenance reconstructed by the Tracer. Z, MET, W-muon and three-lepton quantities are traced to the same expressions used in the code.
- **Run 02:** `z_masses.append(z_mass)` around line 300; histogram uses a shared plotting helper around lines 334–351 with no `range=(60,120)`. The Tracer names `z_masses` as plot input and does not fabricate the missing range argument.
- **Run 08:** `z_mass_list.append(z_mass)` at line 297; shared plotting helper near lines 335–344 also has no 60–120 range argument. Again this is a generation-vs-spec discrepancy.
- **Run 07:** `final_output.txt` is identical to Run 03 and contains ten plot entries; reduction to 14 CSV requirements is an artifact of requirement grouping in Luna screening.

## Provisional Table 12 counts for Case 4

| Runs | Requirements | Runs with ≥1 tracer issue | Hallucination | Dependency error | Source error | Coverage miss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 238 | 0 | 0 | 0 | 0 | 0 |

This reproduces the published Case 4 row, subject to expert confirmation. Do **not** label it human-adjudicated until that confirmation is made.

## Storage and procedure

Keep original `paper_data/tracer_evaluation/14B/*.csv` unchanged. Store this review in `recalculation/table12/review/` and commit it separately. Use `expert_confirmation` and `expert_note` for the researcher's sign-off rather than editing the Luna fields.
