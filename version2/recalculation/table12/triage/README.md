# Table 12: provisional issue-family triage of Luna screening

## Source and scope

Input: `recalculation/table12/results/high_priority_review.csv` (240 rows from the existing 50-run Qwen3-14B screening).

This is **not** a fresh evaluation of the generated Python source code, and it is **not** expert adjudication. It only classifies the explanations already present in the Luna evaluation CSV. No API calls are performed. No source data are modified.

## Files

- `all_240_triaged.csv`: every original row plus `triage_group`, `provisional_action`, `triage_reason` and explicitly unreviewed status fields.
- `issue_groups.csv`: one row per issue family, with counts and a representative example.
- `targeted_and_spotcheck_queue.csv`: a narrower provisional queue; **not all its rows require independent human review**. Inspect groups and representative runs first.
- `review_examples_by_group.csv`: up to two different runs per issue family for checking the original code and tracer.

## Provisional classification

- `exception_candidate`: a note likely addressed by E1, E3 or E4, subject to checking the underlying condition. In particular, E3 only applies if the scientific plotted quantity and its provenance are identified; E4 does not exempt errors in cut-boundary semantics (E6).
- `targeted`: notes alleging a concrete false code/trace relationship (e.g. nonexistent composite object, false helper dependency, equality boundary). Review a few concrete run examples, then decide whether the rule generalizes to remaining runs. Extra claims must not be double counted with their matching requirement rows.
- `spotcheck`: notes that need source inspection or cannot be classified confidently from the text alone.

These are **provisional screening actions**, not final error counts or changed Table 12 statistics. Human review status is deliberately `not_reviewed`. Never infer human confirmation from this sheet. After checking the source, record a decision in a separate reviewer decision log.

## Run again locally (from workbench root)

```bash
python3 recalculation/table12/triage_high_priority.py \
    --input recalculation/table12/results/high_priority_review.csv \
    --out recalculation/table12/triage
```

The above reads only CSV and produces output in `triage/`.
