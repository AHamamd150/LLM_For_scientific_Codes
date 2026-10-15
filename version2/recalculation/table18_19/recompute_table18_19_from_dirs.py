#!/usr/bin/env python3
"""Recompute Tables 18/19 from unpacked Oracle-lite run directories.

Read-only inputs. Writes *new* output filenames under recalculation/table18_19/results.
Standard-library only; no LLM calls, network calls, copying, or moving files.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "paper_data" / "runs" / "oracle_lite"
EVAL = ROOT / "paper_data" / "oracle_evaluation"
OUT = ROOT / "recalculation" / "table18_19" / "results"

RUN_DIR = {
    4: RUNS / "oracle_lite_v4_32b_10runs",
    5: RUNS / "oracle_lite_v5_32b_10runs",
}
ENGLISH = EVAL / "oracle_lite_v5_32b_10runs_issues_classified_english.csv"
KNOWLEDGE_AXES = EVAL / "oracle_lite_v5_32b_10runs_issues_classified_v4_knowledge_axes.csv"

CLASS_MAP = {
    "genuine unresolved": "Genuine unresolved tasks",
    "Genuine unresolved choice": "Genuine unresolved tasks",
    "physics caution": "Physics caution",
    "Physics caution": "Physics caution",
    "resolved by prompt": "Resolved by prompt",
    "Resolved by prompt": "Resolved by prompt",
    "invented": "Invented alternative",
    "Invented alternative": "Invented alternative",
}
KNOWLEDGE_MAP = {
    "なし": "None", "低": "Low", "中": "Medium", "高": "High",
    "None": "None", "Low": "Low", "Medium": "Medium", "High": "High",
}
CLASS_ORDER = ["Genuine unresolved tasks", "Physics caution", "Resolved by prompt", "Invented alternative"]
KNOWLEDGE_ORDER = ["None", "Low", "Medium", "High"]


def write_csv(filename: str, header: list[str], rows: list[list]):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def candidate_counts(version: int) -> list[tuple[int, int, int]]:
    source_dir = RUN_DIR[version]
    if not source_dir.is_dir():
        raise FileNotFoundError(
            f"Expected unpacked V{version} run directory: {source_dir}\n"
            "Copy the original run directory into paper_data/runs/oracle_lite/ first; do not rename case or response files."
        )
    item = "CANDIDATE" if version == 4 else "UNDERSPECIFICATION"
    expr = re.compile(r"^\s*\[" + item + r"\s+(\d+)\]", re.MULTILINE)
    rows = []
    for case in range(1, 8):
        for run in range(1, 11):
            source = source_dir / f"case{case}" / f"response_{run:03d}.txt"
            if not source.is_file():
                raise FileNotFoundError(f"Expected V{version} input file: {source}")
            content = source.read_text(encoding="utf-8-sig")
            nums = [int(n) for n in expr.findall(content)]
            if nums != list(range(1, len(nums) + 1)):
                raise ValueError(f"{source}: unexpected or nonsequential candidate headings: {nums}")
            if not nums:
                raise ValueError(f"{source}: no candidate headings found")
            if version == 5 and len(nums) > 3:
                raise ValueError(f"{source}: V5 produced more than three candidates")
            rows.append((case, run, len(nums)))
    assert len(rows) == 70
    return rows


def read_classification(path: Path) -> dict[tuple[int, int, int], tuple[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Classification CSV not found: {path}")
    is_japanese = path == KNOWLEDGE_AXES
    case_col, run_col, item_col = ("case", "run", "item") if is_japanese else ("Case", "Run", "Item")
    category_col = "判定" if is_japanese else "Classification"
    knowledge_col = (
        "HELPER_REGISTRY外domain knowledge（なし・低・中・高）"
        if is_japanese else "Domain knowledge beyond HELPER_REGISTRY"
    )
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = (case_col, run_col, item_col, category_col, knowledge_col)
        missing = [k for k in required if k not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns: {missing}")
        output = {}
        for r in reader:
            key = tuple(int(r[k]) for k in (case_col, run_col, item_col))
            if key in output:
                raise ValueError(f"{path}: duplicate classification for {key}")
            try:
                classification = CLASS_MAP[r[category_col].strip()]
                knowledge = KNOWLEDGE_MAP[r[knowledge_col].strip()]
            except KeyError as e:
                raise ValueError(f"{path}: unexpected classification at {key}: {e}") from e
            output[key] = (classification, knowledge)
    return output


def main():
    # Validate all inputs and any two available classification sheets BEFORE creating output files.
    c4 = candidate_counts(4)
    c5 = candidate_counts(5)
    if KNOWLEDGE_AXES.is_file() and ENGLISH.is_file():
        v4_axes = read_classification(KNOWLEDGE_AXES)
        english = read_classification(ENGLISH)
        if v4_axes != english:
            mismatch = set(v4_axes) ^ set(english)
            value_mismatch = [key for key in (v4_axes.keys() & english.keys()) if v4_axes[key] != english[key]]
            raise ValueError(f"Two classification CSVs disagree: keys={sorted(mismatch)[:5]}, values={sorted(value_mismatch)[:5]}")
        print("Classification cross-check: final knowledge-axes and English CSV agree item-by-item.")
        classification = v4_axes
        classification_source = KNOWLEDGE_AXES
    elif KNOWLEDGE_AXES.is_file():
        classification = read_classification(KNOWLEDGE_AXES)
        classification_source = KNOWLEDGE_AXES
    else:
        classification = read_classification(ENGLISH)
        classification_source = ENGLISH

    expected_keys = {
        (case, run, item)
        for case, run, count in c5
        for item in range(1, count + 1)
    }
    if set(classification) != expected_keys:
        missing, surplus = expected_keys - set(classification), set(classification) - expected_keys
        raise ValueError(f"V5 response/classification mismatch: missing={sorted(missing)[:8]}, extra={sorted(surplus)[:8]}")
    if len(classification) != 208:
        raise ValueError(f"Unexpected V5 classification count: {len(classification)} (expected 208)")

    t18 = []
    for case in range(1, 8):
        counts = [num for c, run, num in c4 if c == case]
        t18.append([case, len(counts), sum(counts), f"{sum(counts) / len(counts):.1f}"])
    total = sum(n for c, r, n in c4)
    t18.append(["Total", 70, total, f"{total / 70:.2f}"])

    matrix = Counter(classification.values())
    t19 = []
    for cls in CLASS_ORDER:
        cells = [matrix[(cls, knowledge)] for knowledge in KNOWLEDGE_ORDER]
        t19.append([cls, *cells, sum(cells)])
    col_totals = [sum(matrix[(cls, kn)] for cls in CLASS_ORDER) for kn in KNOWLEDGE_ORDER]
    t19.append(["Total", *col_totals, len(classification)])

    write_csv("table18_from_directories.csv", ["Case", "Runs", "Total candidates", "Candidates/run"], t18)
    write_csv("table19_from_directories.csv", ["Issue class", *KNOWLEDGE_ORDER, "Total"], t19)
    write_csv("v4_candidate_counts_by_run_from_directories.csv", ["Case", "Run", "Candidates"], [list(x) for x in c4])
    write_csv("v5_candidate_counts_by_run_from_directories.csv", ["Case", "Run", "Candidates"], [list(x) for x in c5])
    print("Table 18 — V4 unrestricted candidates:")
    for r in t18:
        print("  " + ", ".join(map(str, r)))
    print("Table 19 — V5 classified candidates:")
    for r in t19:
        print("  " + ", ".join(map(str, r)))
    print(f"Validated: V4 70 runs, {total} candidates; V5 70 runs, {len(classification)} candidates.")
    print(f"Classification source: {classification_source}")
    print(f"Saved new result files under: {OUT}")


if __name__ == "__main__":
    main()
