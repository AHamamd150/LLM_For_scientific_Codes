#!/usr/bin/env python3
"""Recompute Appendix Table 12 from frozen Luna primary CSVs and expert decision addendum.

From the workbench root:
  python3 recalculation/table12/recompute_table12.py

This script never executes an LLM or modifies the archived input CSVs.
It aggregates explicit reviewed issues. The remaining screening rows are not
represented as exhaustively human-reviewed; see TABLE12_RECOUNT_NOTES.md.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from pathlib import Path

CATEGORIES = ('Hallucination', 'Dependency error', 'Source error', 'Coverage miss')
EXPECTED_REQ = {1:247, 2:238, 3:311, 4:238, 5:269}
EXPECTED_RUNS = 10

def load_csv(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, headers):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-dir',type=Path, default=Path('paper_data/tracer_evaluation/14B'))
    here=Path(__file__).resolve().parent
    ap.add_argument('--decisions',type=Path, default=here/'review/table12_adjudication_addendum.csv')
    ap.add_argument('--out-dir',type=Path,default=here/'results')
    args=ap.parse_args()
    decisions=load_csv(args.decisions)
    decision_by_key={}
    for d in decisions:
        key=(int(d['case']),int(d['run']),d['req_id'])
        if key in decision_by_key:
            raise ValueError(f'duplicate decision: {key}')
        if d['decision'] not in ('count','accept'):
            raise ValueError(f'unknown decision {key}: {d["decision"]}')
        if d['decision']=='count' and d['issue_type'] not in CATEGORIES:
            raise ValueError(f'unknown issue type {key}: {d["issue_type"]}')
        decision_by_key[key]=d
    result=[]
    counted=[]
    found=set()
    total_req=0
    total_runs_with_issue=0
    for case in range(1,6):
        n_req=0
        case_issues=[]
        for run in range(1,EXPECTED_RUNS+1):
            source=args.input_dir/f'case{case}_run{run:02d}.csv'
            if not source.exists():
                raise FileNotFoundError(source)
            data=load_csv(source)
            keys=set()
            for r in data:
                if r['row_type']=='requirement':
                    n_req+=1
                key=(case,run,r['req_id'])
                if key in keys:
                    raise ValueError(f'Duplicate ID in {source}: {r["req_id"]}')
                keys.add(key)
                if key in decision_by_key:
                    found.add(key)
                    d=decision_by_key[key]
                    if r['row_type']!='requirement':
                        raise ValueError(f'Not a requirement row: {key}')
                    if d['decision']=='count':
                        case_issues.append(d)
                        counted.append(d)
        if n_req!=EXPECTED_REQ[case]:
            raise ValueError(f'Case {case}: expected {EXPECTED_REQ[case]} requirements, got {n_req}')
        caseset={int(d['run']) for d in case_issues}
        total_runs_with_issue+=len(caseset)
        total_req+=n_req
        counts={cat:sum(d['issue_type']==cat for d in case_issues) for cat in CATEGORIES}
        result.append({'Case':case,'Runs':EXPECTED_RUNS,'Req. items':n_req,
               'Runs with >=1 issue':len(caseset),**counts})
    if found != set(decision_by_key):
        missing=set(decision_by_key)-found
        raise ValueError(f'Decisions absent from primary CSVs: {sorted(missing)}')
    total={'Case':'Total','Runs':5*EXPECTED_RUNS,'Req. items':total_req,'Runs with >=1 issue':total_runs_with_issue}
    for cat in CATEGORIES:
        total[cat]=sum(d['issue_type']==cat for d in counted)
    result.append(total)
    headers=['Case','Runs','Req. items','Runs with >=1 issue',*CATEGORIES]
    write_csv(args.out_dir/'table12_recomputed.csv',result,headers)
    write_csv(args.out_dir/'table12_counted_items.csv',counted,list(decisions[0]))
    print(', '.join(headers))
    for row in result: print(', '.join(str(row[k]) for k in headers))
    print(f'Validated {total_req} requirement rows across 50 run CSVs; '
          f'{len(counted)} counted issues; {len(decisions)-len(counted)} accepted exceptions.')
    print(f'Wrote results under: {args.out_dir}')

if __name__=='__main__':
    main()
