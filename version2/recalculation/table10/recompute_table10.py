#!/usr/bin/env python3
"""Recompute Appendix Table 10 from frozen run helper-selection JSON files.

Usage (from the workbench repository root):
    python3 recalculation/table10/recompute_table10.py frozen_timing

The input tree must contain run_01/case1/helpers/selection.json, etc.
Outputs are written only under --out (the input tree is not modified).
"""

import argparse
import csv
import itertools
import json
import statistics
from collections import Counter
from pathlib import Path


# Required infrastructure, not a task-selected helper.
EXCLUDED_HELPERS = {"lhco_reco"}


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path, help="Directory containing run_01, run_02, ...")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results",
                        help="Output directory (default: table10/results alongside this script)")
    parser.add_argument("--cases", default="1,2,3,4,5")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument(
        "--exclude-helpers", default=",".join(sorted(EXCLUDED_HELPERS)),
        help="Comma-separated names to omit from all helper-selection statistics "
             "(default: lhco_reco)",
    )
    args = parser.parse_args()
    cases = [int(s.strip()) for s in args.cases.split(",")]
    excluded = {s.strip() for s in args.exclude_helpers.split(",") if s.strip()}
    if args.runs < 2:
        parser.error("--runs must be at least 2 for pairwise Jaccard")

    summaries, runs, pairs, frequencies = [], [], [], []
    for case in cases:
        sets = {}
        for run_number in range(1, args.runs + 1):
            run = f"run_{run_number:02d}"
            relpath = Path(run) / f"case{case}" / "helpers" / "selection.json"
            path = args.run_root / relpath
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                parser.error(f"Cannot load {path}: {exc}")
            selected = data.get("selected_helpers")
            if not isinstance(selected, list) or not all(
                isinstance(entry, dict) and isinstance(entry.get("name"), str)
                for entry in selected
            ):
                parser.error(f"Malformed selected_helpers in {path}")
            names = [entry["name"] for entry in selected]
            if len(names) != len(set(names)):
                parser.error(f"Duplicate selected helper names in {path}")
            selected_names = set(names) - excluded
            sets[run] = selected_names
            runs.append({
                "case": case, "run": run, "n_helpers": len(selected_names),
                "helpers": ";".join(sorted(selected_names)), "source_file": relpath.as_posix()
            })

        all_sets = list(sets.values())
        common = set.intersection(*all_sets)
        union = set.union(*all_sets)
        pair_values = []
        for a, b in itertools.combinations(sorted(sets), 2):
            both = sets[a] & sets[b]
            either = sets[a] | sets[b]
            similarity = len(both) / len(either) if either else 1.0
            pair_values.append(similarity)
            pairs.append({
                "case": case, "run_a": a, "run_b": b,
                "intersection": len(both), "union": len(either),
                "jaccard": f"{similarity:.6f}"
            })

        counts = Counter(h for helpers in all_sets for h in helpers)
        for helper in sorted(union):
            frequencies.append({
                "case": case, "helper": helper, "count": counts[helper],
                "n_runs": args.runs, "fraction": f"{counts[helper]/args.runs:.6f}"
            })
        sizes = [len(s) for s in all_sets]
        summary = {
            "case": case, "n_runs": args.runs,
            "common": len(common), "non_common": len(union - common),
            "min_per_run": min(sizes), "max_per_run": max(sizes),
            "mean_helpers_per_run": f"{statistics.mean(sizes):.3f}",
            "mean_pairwise_jaccard": f"{statistics.mean(pair_values):.6f}",
            "sd_pairwise_jaccard": f"{statistics.stdev(pair_values):.6f}",
            "min_pairwise_jaccard": f"{min(pair_values):.6f}",
            "max_pairwise_jaccard": f"{max(pair_values):.6f}",
            "common_helpers": ";".join(sorted(common)),
            "non_common_helpers": ";".join(sorted(union - common)),
        }
        summaries.append(summary)
        print(f"Case {case}: {len(common)} common, {len(union-common)} non-common; "
              f"{min(sizes)}–{max(sizes)} helpers/run; "
              f"mean Jaccard={statistics.mean(pair_values):.3f}")

    args.out.mkdir(parents=True, exist_ok=True)
    for filename, data in (
        ("helper_stability_summary.csv", summaries),
        ("run_helper_sets.csv", runs),
        ("pairwise_jaccard.csv", pairs),
        ("helper_frequencies.csv", frequencies),
    ):
        write_csv(args.out / filename, list(data[0]), data)
    print(f"Saved 4 CSV files under: {args.out}")


if __name__ == "__main__":
    main()
