# Recompute Tables 18–19 after moving Oracle-lite run folders

This is an **additive, script-only update**. It does **not** include, copy, move, delete, or overwrite any raw Oracle-lite experimental outputs or human adjudication CSVs. The existing `recompute_table18_19.py` remains unchanged. Only the four **newly named** result CSVs are written by this script.

## Expected layout at the `test_runs` root

```text
paper_data/
  runs/oracle_lite/
    oracle_lite_v4_32b_10runs/case1/response_001.txt ... case7/response_010.txt
    oracle_lite_v5_32b_10runs/case1/response_001.txt ... case7/response_010.txt
  oracle_evaluation/
    oracle_lite_v5_32b_10runs_issues_classified_english.csv
    # optional: oracle_lite_v5_32b_10runs_issues_classified_v4_knowledge_axes.csv
recalculation/table18_19/
  recompute_table18_19.py               # existing script, not touched
  recompute_table18_19_from_dirs.py     # new script
  README_from_directories.md            # this file
  results/
```

Copy the original v4/v5 run directories and the English classification CSV into the locations shown; retain their source copies until the results have been checked. The CSV may also be retained inside the v5 run folder, but the script reads it only from `paper_data/oracle_evaluation/`. If both English and `v4_knowledge_axes` classification files are present in `oracle_evaluation/`, the script verifies that all 208 `(case, run, item)` classifications and knowledge levels agree, using `v4_knowledge_axes` as the primary source. If only English is present, it is sufficient, because its classification/knowledge fields agree with `v4_knowledge_axes` for all 208 records in the supplied source files.

## Run

From any directory, using Python 3.9+:

```bash
python3 recalculation/table18_19/recompute_table18_19_from_dirs.py
```

The script will validate that all 70 V4 and all 70 V5 response files exist, heading numbers are sequential, V5 contains at most three items/run, and that all 208 classifications map to the V5 response items. It uses Python standard library only, makes no model/API calls, and never writes to `paper_data`.

It creates or replaces **only** these derived result files in `recalculation/table18_19/results/`:

- `table18_from_directories.csv`
- `table19_from_directories.csv`
- `v4_candidate_counts_by_run_from_directories.csv`
- `v5_candidate_counts_by_run_from_directories.csv`

Expected total candidate counts: V4 584, V5 208. Table 19 expected totals: Genuine 47, Physics caution 11, Resolved 143, Invented 7. Both tables should reproduce the existing manuscript numbers. Table 20 is separate and not covered here.

The two distinct "v4" labels must not be confused: `oracle_lite_v4_32b_10runs` is the unrestricted *experiment version*, whereas `v4_knowledge_axes.csv` is the final revision of the V5 *classification sheet*.
