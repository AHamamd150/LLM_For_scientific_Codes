# Appendix recalculation (workbench Version 2)

This directory contains **only** scripts and evaluation inputs for recomputing
Appendix tables. It does not replace the raw generated analyses. All commands
below are executed from the `test_runs` repository root.

## Layout

```text
recalculation/
├── README.md
├── table10/
│   ├── recompute_table10.py
│   └── results/                 # generated CSV files
└── table11/
    ├── recompute_table11.py
    ├── input/
    │   └── case2_case6_implementation_run_level.csv
    └── results/                 # generated summary CSV
```

## Table 10 — helper selection stability

```bash
python3 recalculation/table10/recompute_table10.py frozen_timing
cat recalculation/table10/results/helper_stability_summary.csv
```

Input: `frozen_timing/run_01` ... `run_10`, cases 1–5,
with each run supplying `caseN/helpers/selection.json`.
The script reads these **50 JSON files** directly; it does not use previous
summary CSV files as inputs. The mandatory `lhco_reco` module is excluded from
all helper statistics. Mean pairwise Jaccard averages all **45 unordered pairs**
for each case, without self-pairs.

Outputs in `table10/results/`:

- `helper_stability_summary.csv`
- `helper_frequencies.csv`
- `pairwise_jaccard.csv`
- `run_helper_sets.csv`

Table 10 in the current manuscript (cases 1–5) is expected to have mean Jaccard
values 1.000, 0.949, 1.000, 0.970, and 1.000 respectively.

## Table 11 — implementation issue counts

```bash
python3 recalculation/table11/recompute_table11.py
cat recalculation/table11/results/table11_recomputed.csv
```

Input: `table11/input/case2_case6_implementation_run_level.csv` (30 human-
judged run-level records: 10 each for Case 2 / 14B, Case 2 / 32B,
and Case 6 / 32B).

This script checks coverage of the expected runs, duplicate identifiers,
binary flags, and consistency of the per-run `any_listed_issue` flag,
then aggregates the existing labels. **It does not independently verify the
semantic annotations against the generated code.** The evidence and source
paths in the run-level input CSV should be retained for traceability.

The script writes `table11/results/table11_recomputed.csv`.

## Data handling

- Source directories such as `frozen_timing/` are read-only to these scripts.
- Outputs are confined to the corresponding `results/` directory by default.
- Scripts and their inputs can be committed; do not mix in unused Oracle v1–v3
  records or Version 1 legacy data.
- Before relocating source run directories, check source paths in the manual
  Table 11 CSV; its evidence links reflect the evaluation's original layout.
