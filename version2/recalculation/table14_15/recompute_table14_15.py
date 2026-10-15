#!/usr/bin/env python3
"""Recompute Appendix Tables 14–15 from E6 run-level adjudication CSV.

Run from the workbench repository root:
    python3 recalculation/table14_15/recompute_table14_15.py

This script reads existing data only and never calls a model or modifies run outputs.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

CLASS_MAP = {
    "complete": ("Pass", "yes", "yes"),
    "partial_condition_only": ("Partial", "yes", "no"),
    "partial_quantity_only": ("Fail", "no", "no"),
    "na": ("N/A", "n/a", "n/a"),
}
DETAIL_CLASSES = list(CLASS_MAP)
SUMMARY_CLASSES = ["Pass", "Partial", "Fail", "N/A"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("Empty input CSV")
    required = {"model", "case", "run", "condition_id", "cut_type", "e6_detail_class",
                "paper_summary_class", "boundary_recovered", "control_flow_semantics_complete",
                "include_in_global_14B_E6_table", "include_in_case_model_E6_comparison"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    seen: set[tuple[str, ...]] = set()
    for i, row in enumerate(rows, start=2):
        key = tuple(row[k] for k in ("model", "case", "run", "condition_id"))
        if key in seen:
            raise ValueError(f"Duplicate model/case/run/condition_id at row {i}: {key}")
        seen.add(key)
        cls = row["e6_detail_class"]
        if cls not in CLASS_MAP:
            raise ValueError(f"Unknown E6 class at row {i}: {cls}")
        got = tuple(row[k] for k in ("paper_summary_class", "boundary_recovered",
                                      "control_flow_semantics_complete"))
        if got != CLASS_MAP[cls]:
            raise ValueError(f"Inconsistent E6 labels at row {i}: {got} vs {CLASS_MAP[cls]}")
        if row["include_in_global_14B_E6_table"] == "yes" and row["model"] != "14B":
            raise ValueError(f"Non-14B item in Table 14 at row {i}")
        if row["include_in_case_model_E6_comparison"] == "yes" and row["cut_type"] != "two-sided window":
            raise ValueError(f"Non-two-sided cut in Table 15 at row {i}")
    return rows


def save_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def aggregate14(rows):
    result = []
    for label, group in [
        ("Two-sided window", [r for r in rows if r["cut_type"] == "two-sided window"]),
        ("Lower-bound only", [r for r in rows if r["cut_type"] == "lower-bound only"]),
        ("Total", rows),
    ]:
        ct = Counter(r["e6_detail_class"] for r in group)
        result.append({"Cut type": label, "Items": len(group),
                       "Complete semantic capture": ct["complete"],
                       "Partial: condition only": ct["partial_condition_only"],
                       "Partial: quantity only": ct["partial_quantity_only"], "N/A": ct["na"]})
    return result


def aggregate15(rows):
    result = []
    specs = [("14B", str(i)) for i in range(1, 6)] + [("14B", "Total"), ("32B", "2"), ("32B", "6")]
    for model, case in specs:
        selected = [r for r in rows if r["model"] == model and
                    (r["case"] == case or (case == "Total" and model == "14B"))]
        c = Counter(r["paper_summary_class"] for r in selected)
        evaluated = len(selected) - c["N/A"]
        recovery = (c["Pass"] + c["Partial"]) / evaluated * 100 if evaluated else 0.0
        result.append({"Model": model, "Case": case, "Pass": c["Pass"],
                       "Partial": c["Partial"], "Fail": c["Fail"], "N/A": c["N/A"],
                       "Evaluated (excl. N/A)": evaluated, "Recovery rate": f"{recovery:.1f}%"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("paper_data/tracer_evaluation/E6_run_level_current.csv"))
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results")
    args = parser.parse_args()
    rows = read_rows(args.input)
    t14rows = [r for r in rows if r["include_in_global_14B_E6_table"] == "yes"]
    t15rows = [r for r in rows if r["include_in_case_model_E6_comparison"] == "yes"]
    if len(rows) != 130 or len(t14rows) != 90 or len(t15rows) != 110:
        raise ValueError(f"Unexpected row counts: all={len(rows)}, Table14={len(t14rows)}, Table15={len(t15rows)}")
    a = aggregate14(t14rows)
    b = aggregate15(t15rows)
    save_csv(args.out / "table14_recomputed.csv", list(a[0]), a)
    save_csv(args.out / "table15_recomputed.csv", list(b[0]), b)
    print("Table 14 — 14B E6 classification:")
    for r in a:
        print(f"  {r['Cut type']}: {r['Items']} items; complete={r['Complete semantic capture']}, "
              f"partial-condition={r['Partial: condition only']}, partial-quantity={r['Partial: quantity only']}, N/A={r['N/A']}")
    print("Table 15 — two-sided windows by model/case:")
    for r in b:
        print(f"  {r['Model']} Case {r['Case']}: pass={r['Pass']}, partial={r['Partial']}, "
              f"fail={r['Fail']}, N/A={r['N/A']}, evaluated={r['Evaluated (excl. N/A)']}, recovery={r['Recovery rate']}")
    print(f"Saved: {args.out / 'table14_recomputed.csv'}")
    print(f"Saved: {args.out / 'table15_recomputed.csv'}")

if __name__ == "__main__":
    main()
