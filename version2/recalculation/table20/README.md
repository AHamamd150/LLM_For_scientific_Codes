# Table 20 recalculation (Oracle-lite V4/V5)

The script `recompute_table20.py` reconstructs the 18 rows of manuscript Table 20 from the original archived evaluation CSVs. It performs **no API calls**, does not alter experiments, and does not change any source CSV.

## Inputs

* `paper_data/oracle_evaluation/oracle_lite_v4_32b_predefined_issue_summary.csv` — original 18 issue-level detection totals out of 10 V4 unrestricted runs. **This is already adjudicated summary data**, not run-level labels. This script checks and republishes these detection counts, but cannot independently verify them against V4 raw outputs.
* `paper_data/oracle_evaluation/oracle_lite_v5_predefined_v4_issue_summary.csv` — original V5 18-issue summary with class breakdown.
* `paper_data/oracle_evaluation/oracle_lite_v5_32b_10runs_issues_classified_clean.csv` — V5 208 candidate-level adjudications, including Case, Run, Item, class and benchmark match(es).

The source experiment runs under `paper_data/runs/oracle_lite/` are not touched or required for this recount.

## Run

From `test_runs` repository root:

```sh
python3 recalculation/table20/recompute_table20.py
```

Outputs under `recalculation/table20/results/`:

- `table20_recomputed.csv` — 18 rows displayed in Table 20.
- `table20_v5_classification_breakdown.csv` — class breakdown for each predefined benchmark issue.
- `table20_v5_double_matches.csv` — V5 candidates linked to two benchmark issues.

## Counting convention and caveat

V4 extensive detection is counted **per run** (10 runs per case). V5 appearance is counted **per reported issue occurrence** (29 items in Cases 1 and 6; 30 in other cases). The V5 208 candidate rows contain 54 rows with ≥1 predefined issue match, but three candidates each match **two** benchmark issues, producing 57 issue appearances. This is not the number of genuine-unresolved candidates: the 57 appearances include other adjudication classes (e.g. resolved by prompt or invented alternative).

Do not describe the V5 appearances as all genuinely unresolved choices. To audit V4 issue-level detection at run level, separately retrieve the historical V4 run-level matching sheet or manually re-annotate the saved V4 outputs; this script does not assert that such source judgments were independently verified.
