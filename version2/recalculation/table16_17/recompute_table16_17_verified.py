#!/usr/bin/env python3
"""Recompute Tables 16 and 17 using the verified 210-row run-level CSV only.

Uses Python's standard library. No LLM/API call, no source CSV modification,
no dependency on the older 16-row summary, no overwrites of prior results.

All per-run outcomes originate from the archived adjudications; this script
aggregates those records rather than independently auditing generated code.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "paper_data/tracer_evaluation/critique_summary"
    / "case2_6_case5_7_run_level_adjudication_verified.csv"
)
RESULTS = Path(__file__).resolve().parent / "results"

# (issue as written in Table 16/17, setting, issue_id)
TABLE16 = [
    ("Closest b-jet replaced by leading b-jet", "Case 2 / 14B", "closest_b_leading_instead"),
    ("Closest b-jet replaced by leading b-jet", "Case 6 / 14B", "closest_b_leading_instead"),
    ("Closest b-jet replaced by leading b-jet", "Case 6 / 32B", "closest_b_leading_instead"),
    ("Muon eta threshold mismatch", "Case 2 / 14B", "muon_eta_mismatch"),
    ("Muon eta threshold mismatch", "Case 6 / 14B", "muon_eta_mismatch"),
    ("Muon eta threshold mismatch", "Case 6 / 32B", "muon_eta_mismatch"),
    ("Unrequested top-mass cut", "Case 2 / 14B", "extra_top_mass_cut"),
    ("Unrequested top-mass cut", "Case 6 / 14B", "extra_top_mass_cut"),
    ("Unrequested DeltaR(l,b) < 0.5 cut", "Case 6 / 14B", "unrequested_dr_lb_cut"),
    ("Unrequested DeltaR(l,b) < 0.5 cut", "Case 6 / 32B", "unrequested_dr_lb_cut"),
]
TABLE17 = [
    ("Incorrect ditau-dijet Delta phi", "Case 5 / 14B", "wrong_ditau_dijet_dphi"),
    ("Incorrect ditau-dijet Delta phi", "Case 7 / 14B", "wrong_ditau_dijet_dphi"),
    ("b-jet pre-filter instead of veto", "Case 7 / 32B", "b_veto_prefilter"),
]
# Supplemental rows are not published in Tables 16 or 17.
SUPPLEMENTAL = [
    ("Incorrect ditau-dijet Delta phi", "Case 5 / 14B code + 32B post-review", "wrong_ditau_dijet_dphi"),
    ("Initial cutflow double counting", "Case 5 / 32B", "initial_cutflow_double_count"),
    ("Selection-cut order mismatch", "Case 7 / 32B", "cut_order_mismatch"),
]

COLUMNS = [
    "issue", "setting", "generation_error", "tracer_exposure", "critique_detection", "source"
]
GROUP_COLUMNS = [
    "setting", "issue_id", "runs", "generation_errors", "tracer_exposed",
    "critique_detected_strict", "critique_partial", "critique_missed",
    "error_runs", "tracer_exposed_runs", "critique_strict_runs",
    "critique_partial_runs", "critique_missed_runs"
]


def parse_bit(value: str, *, allow_na: bool) -> int | None:
    value = value.strip()
    if value in ("0", "1"):
        return int(value)
    if allow_na and value in ("", "N/A"):
        return None
    raise ValueError(f"Invalid {'optional ' if allow_na else ''}flag: {value!r}")


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        result = list(csv.DictReader(fh))
    if len(result) != 210:
        raise ValueError(f"Expected 210 issue/run rows, got {len(result)}")
    return result


def run_string(rows: list[dict[str, str]]) -> str:
    return ",".join(str(int(r["run"])) for r in sorted(rows, key=lambda r: int(r["run"])))


def aggregate(group: list[dict[str, str]]) -> dict[str, str | int]:
    if len(group) != 10 or {int(r["run"]) for r in group} != set(range(1, 11)):
        raise ValueError("Every setting/issue group must contain exactly Runs 01–10")
    erroneous = []
    exposed = []
    correct = []
    partial = []
    missed = []
    for row in group:
        gen = parse_bit(row["generation_error"], allow_na=False)
        trace = parse_bit(row["tracer_exposed"], allow_na=True)
        strict = parse_bit(row["critique_detected_strict"], allow_na=True)
        part = parse_bit(row["critique_partial"], allow_na=True)
        verdict = row["critique_outcome"].strip()
        if gen == 0:
            if (trace, strict, part) != (None, None, None) or verdict not in ("", "N/A"):
                raise ValueError(f"Non-applicable error run has downstream labels: {row}")
            continue
        if trace is None or strict is None or part is None:
            raise ValueError(f"Unresolved run-level annotation: {row}")
        valid = {"correct": (1, 0), "partial": (0, 1), "missed": (0, 0)}
        if verdict not in valid or (strict, part) != valid[verdict]:
            raise ValueError(f"Inconsistent Critique outcome: {row}")
        erroneous.append(row)
        if trace:
            exposed.append(row)
        if strict:
            correct.append(row)
        if part:
            partial.append(row)
        if not strict and not part:
            missed.append(row)

    return {
        "runs": len(group),
        "generation_errors": len(erroneous),
        "tracer_exposed": len(exposed),
        "critique_detected_strict": len(correct),
        "critique_partial": len(partial),
        "critique_missed": len(missed),
        "error_runs": run_string(erroneous),
        "tracer_exposed_runs": run_string(exposed),
        "critique_strict_runs": run_string(correct),
        "critique_partial_runs": run_string(partial),
        "critique_missed_runs": run_string(missed),
    }


def row_for_table(issue: str, setting: str, count: dict[str, str | int]) -> dict[str, str]:
    gen = int(count["generation_errors"])
    if gen == 0:
        tracer = "N/A"
        critique = "N/A"
    else:
        tracer = f'{count["tracer_exposed"]}/{gen}'
        strict, partial = count["critique_detected_strict"], count["critique_partial"]
        critique = (
            f"{strict}/{gen} correct + {partial}/{gen} partial" if partial else f"{strict}/{gen}"
        )
    source = "verified run-level adjudication"
    if setting == "Case 6 / 14B" and issue == "Muon eta threshold mismatch":
        source += f'; Critique miss: Run {int(count["critique_missed_runs"]):02d}'
    return {
        "issue": issue, "setting": setting, "generation_error": f"{gen}/10",
        "tracer_exposure": tracer, "critique_detection": critique, "source": source,
    }


def save(path: Path, fields: list[str], rows: list[dict[str, str | int]]) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    data = read_rows(SOURCE)
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, int]] = set()
    for row in data:
        key = (row["setting"], row["issue_id"], int(row["run"]))
        if key in seen:
            raise ValueError(f"Duplicate setting/issue/run: {key}")
        seen.add(key)
        groups[(row["setting"], row["issue_id"])].append(row)
    if len(groups) != 21:
        raise ValueError(f"Expected 21 setting/issue groups, got {len(groups)}")
    all_counts = {key: aggregate(rows) for key, rows in groups.items()}

    published = TABLE16 + TABLE17
    listed = published + SUPPLEMENTAL
    if len(published) != 13 or len(listed) != 16 or len({(s, i) for _, s, i in listed}) != 16:
        raise ValueError("Invalid Table 16/17 issue mapping")
    if not {(s, i) for _, s, i in listed} <= all_counts.keys():
        raise ValueError("One or more mapped groups are missing")

    # The previously aggregate-only 9/10 is now fully determined from the run-level record.
    muon = all_counts[("Case 6 / 14B", "muon_eta_mismatch")]
    if not (
        muon["generation_errors"] == 10
        and muon["tracer_exposed"] == 10
        and muon["critique_detected_strict"] == 9
        and muon["critique_missed_runs"] == "4"
    ):
        raise ValueError("Verified Case 6 / 14B muon eta audit no longer matches the archived result")

    table16 = [row_for_table(issue, setting, all_counts[(setting, code)]) for issue, setting, code in TABLE16]
    table17 = [row_for_table(issue, setting, all_counts[(setting, code)]) for issue, setting, code in TABLE17]
    extra = [row_for_table(issue, setting, all_counts[(setting, code)]) for issue, setting, code in SUPPLEMENTAL]
    group_table = [
        {"setting": setting, "issue_id": issue_id, **all_counts[(setting, issue_id)]}
        for setting, issue_id in sorted(groups.keys())
    ]

    save(RESULTS / "table16_verified_from_runs.csv", COLUMNS, table16)
    save(RESULTS / "table17_verified_from_runs.csv", COLUMNS, table17)
    save(RESULTS / "supplemental_verified_from_runs.csv", COLUMNS, extra)
    save(RESULTS / "all_21_groups_verified_from_runs.csv", GROUP_COLUMNS, group_table)

    for number, table in ((16, table16), (17, table17)):
        print(f"Table {number} ({len(table)} rows):")
        for row in table:
            print(f"  {row['setting']} | {row['issue']} | {row['generation_error']} | "
                  f"{row['tracer_exposure']} | {row['critique_detection']}")
    print("Data: 210 run-level rows; 21 groups of ten runs")
    print("Verified: Case 6 / 14B muon eta = 10/10 generation, 10/10 tracer, 9/10 critique; miss Run 04")
    print("Supplemental: Case 5 / 32B cutflow = 5/10 generation, 0/5 tracer, 0/5 critique (not in tables)")
    print("No aggregate-summary CSV needed. No existing result filenames overwritten.")
    print("Saved:", RESULTS)


if __name__ == "__main__":
    main()
