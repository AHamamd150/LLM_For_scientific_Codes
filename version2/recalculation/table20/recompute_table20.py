#!/usr/bin/env python3
"""Recompute manuscript Table 20 using archived V4 summaries and V5 item adjudication.

Only reads archived CSVs; outputs new CSVs under recalculation/table20/results.
No LLM calls. No source modification. Python standard library only.
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "paper_data" / "oracle_evaluation"
OUTPUT = Path(__file__).resolve().parent / "results"
CLASSES = ("Genuine unresolved choice", "Physics caution", "Resolved by prompt", "Invented alternative")

# Explicit equivalences between the two *human-created* issue-label vocabularies.
# These are issue-ID mappings only. No result numbers are hard-coded.
ISSUE_IDS = {
    (1, "b-veto: selected vs event-level jets"): "C1-b-veto: selected vs event-level jets",
    (1, "leading jets: selected vs full jet collection"): "C1-leading jets: selected vs full collection",
    (1, "definition of the two-jet system"): "C1-two-jet system definition",
    (2, "hadronic W: selected vs full non-b jets"): "C2-hadronic W: selected vs full non-b jets",
    (2, "hadronic top: selected vs full b jets"): "C2-top: selected vs full b jets",
    (2, ">=2 b-jets: collection scope"): "C2->=2 b-jets: collection scope",
    (2, "closest b-jet: collection scope"): "C2-closest b-jet: collection scope",
    (2, "jet collection entering HT"): "C2-HT: jet collection",
    (2, "jet collection entering the jet multiplicity"): "C2-jet multiplicity: jet collection",
    (5, "opposite-sign tau pair / pairing order"): "C5-OS tau pair / pairing order",
    (5, "b-jet veto: collection scope"): "C5-b-veto scope",
    (5, '"summed momentum" vs four-momentum'): 'C5-"summed momentum" vs four-momentum',
    (5, "definition of ditau centrality"): "C5-centrality definition",
    (6, "jet collection entering HT"): "C6-HT: jet collection",
    (6, "jet collection entering the jet multiplicity"): "C6-jet multiplicity: jet collection",
    (7, "opposite-sign tau pair / pairing order"): "C7-OS tau pair / pairing order",
    (7, 'interpretation of "summed momentum"'): 'C7-"summed momentum" meaning',
    (7, "definition of ditau centrality"): "C7-centrality definition",
}

def read_rows(name):
    with (SOURCE / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def write_rows(name, columns, rows):
    with (OUTPUT / name).open("w", encoding="utf-8", newline="") as handle:
        out = csv.DictWriter(handle, fieldnames=columns)
        out.writeheader()
        out.writerows(rows)


def main():
    v4 = read_rows("oracle_lite_v4_32b_predefined_issue_summary.csv")
    v5_summary = read_rows("oracle_lite_v5_predefined_v4_issue_summary.csv")
    v5_items = read_rows("oracle_lite_v5_32b_10runs_issues_classified_clean.csv")
    assert len(v4) == len(v5_summary) == len(ISSUE_IDS) == 18
    assert len(v5_items) == 208

    candidates_by_case = Counter()
    candidate_seen = set()
    matched_count = Counter()
    by_class = defaultdict(Counter)
    multi = []
    for item in v5_items:
        case, run, item_no = map(int, (item["Case"], item["Run"], item["Item"]))
        key = (case, run, item_no)
        if key in candidate_seen:
            raise ValueError(f"Duplicate V5 candidate: {key}")
        candidate_seen.add(key)
        candidates_by_case[case] += 1
        names = [t.strip() for t in item["Predefined v4 issue(s)"].split(";") if t.strip()]
        if int(item["Predefined v4 match count"]) != len(names):
            raise ValueError(f"Mismatch of multi-match count in {key}")
        if (item["Predefined v4 issue match"] == "Yes") != bool(names):
            raise ValueError(f"Mismatch of match flag in {key}")
        if item["Classification"] not in CLASSES:
            raise ValueError(f"Unknown classification in {key}: {item['Classification']}")
        for name in names:
            matched_count[name] += 1
            by_class[name][item["Classification"]] += 1
        if len(names) > 1:
            multi.append({"case":case,"run":run,"item":item_no,"matched_issues":"; ".join(names),"classification":item["Classification"]})
    if set(matched_count) - set(ISSUE_IDS.values()):
        raise ValueError("Unknown V5 predefined issue: " + str(set(matched_count) - set(ISSUE_IDS.values())))
    expected_candidates = {1:29,2:30,3:30,4:30,5:30,6:29,7:30}
    if dict(candidates_by_case) != expected_candidates:
        raise ValueError(f"Unexpected candidate counts per case: {candidates_by_case}")
    if len(multi) != 3:
        raise ValueError(f"Unexpected multi-matched candidate count: {len(multi)}")

    summary = {r["Predefined v4 issue"]: r for r in v5_summary}
    if set(summary) != set(ISSUE_IDS.values()):
        raise ValueError("V5 summary issue IDs do not match V4-to-V5 mapping")
    output = []
    breakdown = []
    for item in v4:
        case = int(item["case"])
        text = item["predefined_issue"]
        issue_id = ISSUE_IDS[case, text]
        source = summary[issue_id]
        expected_v5 = int(source["v5 occurrence"])
        computed = matched_count[issue_id]
        if computed != expected_v5:
            raise ValueError(f"V5 counts mismatch for {issue_id}: {computed} != {expected_v5}")
        for classification in CLASSES:
            if by_class[issue_id][classification] != int(source[classification]):
                raise ValueError(f"V5 classification mismatch for {issue_id}: {classification}")
        detected = int(item["detections"])
        runs = int(item["runs"])
        if runs != 10 or item["detection_fraction"] != f"{detected}/{runs}":
            raise ValueError(f"Unexpected V4 detection fraction for {issue_id}")
        output.append({
            "case":case,
            "benchmark_issue":text,
            "extensive_detection":f"{detected}/{runs}",
            "oracle_lite_appearance":f"{computed}/{candidates_by_case[case]}",
        })
        breakdown.append({"case":case,"issue_id":issue_id,"v5_occurrence":computed,**{
            cl:by_class[issue_id][cl] for cl in CLASSES
        }})
    OUTPUT.mkdir(exist_ok=True, parents=True)
    write_rows("table20_recomputed.csv", list(output[0]), output)
    write_rows("table20_v5_classification_breakdown.csv", list(breakdown[0]), breakdown)
    write_rows("table20_v5_double_matches.csv", ["case","run","item","matched_issues","classification"], multi)
    print("Table 20 (18 rows):")
    for row in output:
        print("  {case}, {benchmark_issue}: extensive={extensive_detection}, oracle-lite={oracle_lite_appearance}".format(**row))
    print("V5: {} candidates, {} matched candidate rows, {} matched issue occurrences ({} double-matches)".format(
        len(v5_items),sum(int(item['Predefined v4 issue match']=='Yes') for item in v5_items),sum(matched_count.values()),len(multi)
    ))
    print("V5 matched-occurrence classification:",dict(Counter({cl:sum(c[cl] for c in by_class.values()) for cl in CLASSES})))
    print("Source limitations: V4 detection counts are read from an archived human-adjudicated summary, not re-adjudicated from V4 raw runs.")
    print("Saved:",OUTPUT)

if __name__ == "__main__":
    main()
