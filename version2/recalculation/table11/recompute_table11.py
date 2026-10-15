#!/usr/bin/env python3
"""Recalculate Appendix Table 11 from run-level implementation judgements.

Only aggregates the manual run-level flags. It does NOT independently audit
or validate the referenced generated Python source code.

Usage:
    python3 recalculation/table11/recompute_table11.py
"""
import argparse
import csv
from pathlib import Path

GROUPS = (
    ("Case 2 / 14B", 2, "14B"),
    ("Case 2 / 32B", 2, "32B"),
    ("Case 6 / 32B", 6, "32B"),
)
FLAGS = (
    ("Leading b-jet instead of closest b-jet", "closest_b_plot_uses_leading_instead_of_closest_issue"),
    ("Top-mass range inconsistent with task-card semantics", "top_100_250_semantics_issue"),
    ("Top-mass histogram not populated", "top_mass_histogram_not_populated_issue"),
    ("Runs with >=1 listed issue", "any_listed_issue"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    script_dir = Path(__file__).resolve().parent
    parser.add_argument(
        "input_csv", nargs="?", type=Path,
        default=script_dir / "input" / "case2_case6_implementation_run_level.csv",
        help="Run-level manual-judgement CSV (default: bundled table11/input CSV)",
    )
    parser.add_argument(
        "--out", type=Path,
        default=script_dir / "results" / "table11_recomputed.csv",
        help="Output CSV (default: table11/results alongside this script)",
    )
    args = parser.parse_args()

    with args.input_csv.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"model", "case", "run"} | {key for _, key in FLAGS}
        if not required.issubset(set(reader.fieldnames or [])):
            parser.error(f"Missing columns: {sorted(required - set(reader.fieldnames or []))}")
        records = list(reader)

    groups = {}
    for record in records:
        case = int(record["case"])
        model = record["model"].strip()
        run = int(record["run"])
        key = (case, model)
        if key not in {(c, m) for _, c, m in GROUPS}:
            raise ValueError(f"Unexpected case/model: {key}")
        flags = {}
        for _, name in FLAGS:
            value = record[name].strip()
            if value not in ("0", "1"):
                raise ValueError(f"Invalid boolean flag: {name}={value!r} for {key}, run {run}")
            flags[name] = int(value)
        if flags[FLAGS[3][1]] != int(any(flags[n] for _, n in FLAGS[:3])):
            raise ValueError(f"Inconsistent any_listed_issue at {key}, run {run}")
        by_run = groups.setdefault(key, {})
        if run in by_run:
            raise ValueError(f"Duplicate run {run} in {key}")
        by_run[run] = flags

    for label, case, model in GROUPS:
        got = set(groups.get((case, model), {}))
        expected = set(range(1, 11))
        if got != expected:
            raise ValueError(f"{label}: runs missing={sorted(expected-got)}, extra={sorted(got-expected)}")

    output = []
    for issue, name in FLAGS:
        row = {"Implementation issue": issue}
        for label, case, model in GROUPS:
            row[label] = sum(r[name] for r in groups[(case, model)].values())
        output.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    headers = ["Implementation issue"] + [label for label, _, _ in GROUPS]
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output)

    print("Validated 30 unique run-level records, 10 runs per setting.")
    print(", ".join(headers))
    for row in output:
        print(", ".join(str(row[h]) for h in headers))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
