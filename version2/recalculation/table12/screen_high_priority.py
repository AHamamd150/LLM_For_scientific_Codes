#!/usr/bin/env python3
"""Screen 14B tracer pre-annotation CSVs for Table 12 review priorities.

This script makes NO API calls and DOES NOT open or modify generation runs.
It produces a *provisional* review queue, not expert adjudication.

Run from the test_runs repository root:
    python3 recalculation/table12/screen_high_priority.py

To use a different base directory:
    python3 recalculation/table12/screen_high_priority.py --repo-root /path/to/test_runs
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re
import sys

REQUIRED = (
    'case', 'run', 'row_type', 'req_id', 'requirement_or_claim',
    'traced', 'source_correct', 'dependency_correct', 'hallucination', 'note',
)
REVIEW_FIELDS = (
    'priority', 'screening_basis', 'review_flag', 'review_status',
    'pre_adjudication_rule', 'pre_adjudication_note', 'linked_requirement',
    'code_path', 'tracer_path', 'expert_decision', 'expert_evidence',
)
CASE_IDS = (1, 2, 3, 4, 5)
EXPECTED_REQ_ITEMS = 1303  # Published Table 12: check, not an input used in scoring


def read_csv(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f'Empty or invalid CSV: {path}')
        return reader.fieldnames, list(reader)


def write_csv(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def load_reference(path: Path):
    """Optional prior 6-run *worksheet*; NOT a record of human approval."""
    if not path.is_file():
        return {}
    fields, rows = read_csv(path)
    needed = ('case', 'run', 'row_type', 'req_id', 'review_priority', 'review_flag')
    if any(field not in fields for field in needed):
        raise ValueError('Reference worksheet is missing required review columns: ' + str(path))
    lookup = {}
    for row in rows:
        key = (int(row['case']), int(row['run']), row['row_type'], row['req_id'])
        if key in lookup:
            raise ValueError(f'Duplicate reference key {key}')
        lookup[key] = row
    return lookup


def preliminary_screen(row):
    """Conservative flag-only screening; DOES NOT claim to apply E1-E5."""
    reasons = []
    if row['hallucination'].strip().lower() == 'yes':
        reasons.append('hallucination=yes')
    if row['source_correct'].strip().lower() == 'no':
        reasons.append('source_correct=no')
    if row['dependency_correct'].strip().lower() == 'no':
        reasons.append('dependency_correct=no')
    if row['traced'].strip().lower() == 'no' and row['row_type'] == 'requirement':
        reasons.append('traced=no (check E5 against code)')

    # These are *possible* defects; E1-E5 could clear some of them.
    if reasons:
        return 'high', 'raw_flags: ' + '; '.join(reasons)

    uncertain = [f for f in ('source_correct', 'dependency_correct', 'hallucination')
                 if row[f].strip().lower() == 'uncertain']
    if uncertain:
        return 'medium', 'uncertain annotation: ' + ', '.join(uncertain)
    if row['traced'].strip().lower() == 'partial':
        return 'medium', 'traced=partial (inspect E3/E4/E6 applicability)'
    return 'low', 'no adverse raw annotation (not independently verified)'


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--repo-root', type=Path, default=Path('.'))
    p.add_argument('--input-dir', type=Path, help='Overrides the 14B CSV directory')
    p.add_argument('--out', type=Path, help='Directory for new review results')
    p.add_argument('--reference', type=Path, help='Existing 6-run review worksheet (optional)')
    p.add_argument('--allow-partial', action='store_true', help='For testing with fewer than 50 runs')
    args = p.parse_args()

    root = args.repo_root.resolve()
    input_dir = args.input_dir if args.input_dir else root / 'paper_data/tracer_evaluation/14B'
    output_dir = args.out if args.out else root / 'recalculation/table12/results'
    refpath = args.reference if args.reference else root / 'recalculation/table12/review/14B_reference_six_review.csv'
    reference = load_reference(refpath)

    files = sorted(input_dir.glob('case*_run*.csv'))
    if not files:
        p.error(f'No input CSVs found in {input_dir}')
    detected = set()
    all_rows = []
    for file in files:
        match = re.fullmatch(r'case([1-5])_run(\d+)\.csv', file.name)
        if match is None:
            raise ValueError(f'Unexpected input filename: {file.name}')
        case, run = (int(x) for x in match.groups())
        if (case, run) in detected:
            raise ValueError(f'Duplicate case/run files: {(case, run)}')
        detected.add((case, run))
        fields, rows = read_csv(file)
        missing = set(REQUIRED) - set(fields)
        if missing:
            raise ValueError(f'{file}: missing columns {sorted(missing)}')
        rowkeys = set()
        for row in rows:
            if int(row['case']) != case or int(row['run']) != run:
                raise ValueError(f'Incorrect case/run embedded in {file.name}: {row["case"]} {row["run"]}')
            if row['row_type'] not in ('requirement', 'extra_trace_claim'):
                raise ValueError(f'{file}: unknown row_type {row["row_type"]}')
            key = (row['row_type'], row['req_id'])
            if key in rowkeys:
                raise ValueError(f'{file}: duplicate row key {key}')
            rowkeys.add(key)
            if any(row[f].strip().lower() not in {'yes', 'no', 'partial', 'uncertain', 'na', ''}
                   for f in ('traced', 'source_correct', 'dependency_correct', 'hallucination')):
                raise ValueError(f'{file}: invalid annotation value in {key}')
            priority, basis = preliminary_screen(row)
            refkey = (case, run, row['row_type'], row['req_id'])
            old = reference.get(refkey)
            if old is not None:
                if any(old.get(f, '') != row.get(f, '') for f in ('requirement_or_claim', 'traced', 'source_correct', 'dependency_correct', 'hallucination')):
                    raise ValueError(f'Reference/source annotation mismatch: {refkey}')
                priority = old['review_priority'].strip().lower()
                if priority not in ('high', 'medium', 'low'):
                    raise ValueError(f'Unknown priority in reference for {refkey}: {priority}')
                basis = 'six-run worksheet: ' + (old.get('check_category', '') or 'manual screening')
            # This is a triage label, not a completed human judgment.
            all_rows.append({**{f: row.get(f, '') for f in REQUIRED},
                'source_csv': str(file.relative_to(root)) if file.is_relative_to(root) else str(file),
                'priority': priority,
                'screening_basis': basis,
                'review_flag': '要確認' if priority == 'high' else ('参考確認' if priority == 'medium' else '通常'),
                'review_status': '未確認',
                'pre_adjudication_rule': old.get('adjudication_rule', '') if old else '',
                'pre_adjudication_note': old.get('pre_adjudication_note', '') if old else '',
                'linked_requirement': old.get('linked_requirement', '') if old else '',
                'code_path': f'paper_data/runs/14B/frozen_timing/run_{run:02d}/case{case}/execution/generated_analysis.py',
                'tracer_path': f'paper_data/runs/14B/frozen_timing/run_{run:02d}/case{case}/critique/tracer/final_output.txt',
                'expert_decision': '',
                'expert_evidence': '',
            })

    expected_runs = {(case, run) for case in CASE_IDS for run in range(1, 11)}
    if not args.allow_partial and detected != expected_runs:
        missing = sorted(expected_runs - detected)
        surplus = sorted(detected - expected_runs)
        raise ValueError(f'Expected all 50 runs; found {len(detected)}. Missing: {missing}; surplus: {surplus}')
    nreq = sum(row['row_type'] == 'requirement' for row in all_rows)
    nextra = len(all_rows) - nreq
    if not args.allow_partial and nreq != EXPECTED_REQ_ITEMS:
        raise ValueError(f'Expected {EXPECTED_REQ_ITEMS} requirement rows (Table 12), found {nreq}. Check inputs before using the results.')
    if reference and not args.allow_partial:
        observed = {(int(r['case']), int(r['run']), r['row_type'], r['req_id']) for r in all_rows}
        absent = set(reference) - observed
        if absent:
            raise ValueError(f'{len(absent)} reference review rows were not found in source evaluation CSVs: {sorted(absent)[:6]}')

    all_rows.sort(key=lambda r: (int(r['case']), int(r['run']), r['row_type'] != 'requirement',
                                 int(re.sub(r'\D', '', r['req_id']) or '0')))
    high = [row for row in all_rows if row['priority'] == 'high']
    output_fields = list(REQUIRED) + ['source_csv'] + list(REVIEW_FIELDS)
    write_csv(output_dir / 'all_14B_screening.csv', output_fields, all_rows)
    write_csv(output_dir / 'high_priority_review.csv', output_fields, high)

    summary = []
    for case in CASE_IDS:
        sub = [r for r in all_rows if int(r['case']) == case]
        count = Counter(r['priority'] for r in sub)
        highreq = [r for r in sub if r['priority'] == 'high' and r['row_type'] == 'requirement']
        summary.append({'case': case, 'runs': len(set(int(r['run']) for r in sub)),
                        'requirement_items': sum(r['row_type'] == 'requirement' for r in sub),
                        'extra_claims': sum(r['row_type'] == 'extra_trace_claim' for r in sub),
                        'high_requirement_rows': len(highreq),
                        'high_extra_claim_rows': count['high'] - len(highreq),
                        'high_affected_runs': len(set(int(r['run']) for r in sub if r['priority'] == 'high')),
                        'medium_rows': count['medium'], 'low_rows': count['low']})
    write_csv(output_dir / 'summary_by_case.csv', list(summary[0]), summary)
    meta = {'input_csv_files': len(files), 'runs': len(detected), 'requirement_rows': nreq,
            'extra_claim_rows': nextra, 'high_rows': len(high),
            'high_requirement_rows': sum(r['row_type'] == 'requirement' for r in high),
            'high_extra_claim_rows': sum(r['row_type'] == 'extra_trace_claim' for r in high),
            'high_affected_runs': len(set((int(r['case']), int(r['run'])) for r in high)),
            'reference_review_rows_used': sum((int(r['case']), int(r['run']), r['row_type'], r['req_id']) in reference for r in all_rows),
            'reference_worksheet_found': bool(reference),
            'human_adjudication_completed': 0,
            'screening_method': '6-run worksheet priority where available; otherwise conservative raw-flag screening; no code inspection or E1-E5 application on the remaining rows'}
    (output_dir / 'summary.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'Input: {len(files)} CSVs, {len(detected)} runs, {nreq} requirement rows, {nextra} extra claims')
    if not reference:
        print('WARNING: six-run reference worksheet not found. All priorities use raw annotation flags.', file=sys.stderr)
    else:
        print(f'Existing six-run review worksheet applied: {meta["reference_review_rows_used"]} rows')
    print(f'Provisional HIGH: {len(high)} rows ({meta["high_requirement_rows"]} requirement rows; '
          f'{meta["high_extra_claim_rows"]} extra claims), {meta["high_affected_runs"]} affected runs')
    print('No items have been human-adjudicated by this script.')
    print(f'Wrote four result files under {output_dir}')


if __name__ == '__main__':
    main()
