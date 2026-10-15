#!/usr/bin/env python3
"""Reaggregate Tables 16/17 directly from archived per-run adjudications.

Data origin: pre-existing human/LLM adjudication records (not new code auditing).
Exception: Case 6/14B muon threshold Critique 9/10 is still summary-only
because the specific failed run cannot be recovered from the run-level CSV.
Never edits source CSVs or the pre-existing summary recompute script.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / 'paper_data/tracer_evaluation/critique_summary/case2_6_case5_7_run_level_adjudication.csv'
SUMMARY = REPO / 'paper_data/tracer_evaluation/critique_summary/case2_6_case5_7_critique_summary.csv'
OUT = Path(__file__).resolve().parent / 'results'

# ('published issue', 'published setting', 'run-level setting', 'issue_id')
TABLE16 = [
 ('Closest b-jet replaced by leading b-jet','Case 2 / 14B','Case 2 / 14B','closest_b_leading_instead'),
 ('Closest b-jet replaced by leading b-jet','Case 6 / 14B','Case 6 / 14B','closest_b_leading_instead'),
 ('Closest b-jet replaced by leading b-jet','Case 6 / 32B','Case 6 / 32B','closest_b_leading_instead'),
 ('Muon eta threshold mismatch','Case 2 / 14B','Case 2 / 14B','muon_eta_mismatch'),
 ('Muon eta threshold mismatch','Case 6 / 14B','Case 6 / 14B','muon_eta_mismatch'),
 ('Muon eta threshold mismatch','Case 6 / 32B','Case 6 / 32B','muon_eta_mismatch'),
 ('Unrequested top-mass cut','Case 2 / 14B','Case 2 / 14B','extra_top_mass_cut'),
 ('Unrequested top-mass cut','Case 6 / 14B','Case 6 / 14B','extra_top_mass_cut'),
 ('Unrequested DeltaR(l,b) < 0.5 cut','Case 6 / 14B','Case 6 / 14B','unrequested_dr_lb_cut'),
 ('Unrequested DeltaR(l,b) < 0.5 cut','Case 6 / 32B','Case 6 / 32B','unrequested_dr_lb_cut'),
]
TABLE17 = [
 ('Incorrect ditau-dijet Delta phi','Case 5 / 14B','Case 5 / 14B','wrong_ditau_dijet_dphi'),
 ('Incorrect ditau-dijet Delta phi','Case 7 / 14B','Case 7 / 14B','wrong_ditau_dijet_dphi'),
 ('b-jet pre-filter instead of veto','Case 7 / 32B','Case 7 / 32B','b_veto_prefilter'),
]
SPECIAL_SETTING = 'Case 5 / 14B code + 32B post-review'
SPECIAL_SUMMARY_SETTING = 'Same Case 5 / 14B code, 32B post-review'
SUPPLEMENT = [
 ('Incorrect ditau-dijet Delta phi',SPECIAL_SUMMARY_SETTING,SPECIAL_SETTING,'wrong_ditau_dijet_dphi'),
 ('Cutflow bookkeeping / ordering','Case 5 / 32B','Case 5 / 32B','initial_cutflow_double_count'),
 ('Cutflow bookkeeping / ordering','Case 7 / 32B','Case 7 / 32B','cut_order_mismatch'),
]

def readcsv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def writecsv(p,fields,rows):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def flag(x):
    if x is None or not x.strip() or x.strip()=='N/A':return None
    if x in ('1','1.0'):return 1
    if x in ('0','0.0'):return 0
    raise ValueError(f'Invalid flag {x!r}')

def summarize(group):
    assert len(group)==10, f'Expected 10 runs, found {len(group)}'
    assert {int(x['run']) for x in group}==set(range(1,11)), 'Run numbers not 1..10'
    bad=[r for r in group if flag(r['generation_error'])==1]
    for r in group:
        for name in ('generation_error','tracer_exposed','critique_detected_strict','critique_partial'):
            flag(r[name])
        if flag(r['generation_error'])==0:
            assert flag(r['tracer_exposed']) is None and r['critique_outcome'] in ('','N/A') and flag(r['critique_detected_strict']) is None and flag(r['critique_partial']) is None,r
        else:
            assert flag(r['tracer_exposed']) in (0,1),r
            assert r['critique_outcome'] in ('correct','partial','missed','unresolved_run_mapping'),r
            if r['critique_outcome']=='unresolved_run_mapping':
                assert flag(r['critique_detected_strict']) is None and flag(r['critique_partial']) is None,r
            else:
                assert flag(r['critique_detected_strict'])==(r['critique_outcome']=='correct'),r
                assert flag(r['critique_partial'])==(r['critique_outcome']=='partial'),r
    unknown=sum(r['critique_outcome']=='unresolved_run_mapping' for r in bad)
    return dict(generation_errors=len(bad),tracer_exposed=sum(flag(r['tracer_exposed']) for r in bad),
                strict_from_runs=None if unknown else sum(flag(r['critique_detected_strict']) for r in bad),
                partial_from_runs=None if unknown else sum(flag(r['critique_partial']) for r in bad),
                unresolved_count=unknown)

def main():
    data=readcsv(SOURCE)
    assert len(data)==210, f'Unexpected row count: {len(data)}'
    groups=defaultdict(list)
    for row in data:groups[(row['setting'],row['issue_id'])].append(row)
    assert len(groups)==21, f'Unexpected group count: {len(groups)}'
    lookup={k:summarize(g) for k,g in groups.items()}
    source_summary=readcsv(SUMMARY)
    assert len(source_summary)==16
    sr={(r['issue'],r['setting']):r for r in source_summary}
    assert len(sr)==16
    expected=TABLE16+TABLE17+SUPPLEMENT
    assert len(expected)==16
    assert {(x[0],x[1]) for x in expected}==set(sr)
    out16=[];out17=[];outsupp=[]; provenance=[]
    for dest,table in ((out16,TABLE16),(out17,TABLE17),(outsupp,SUPPLEMENT)):
        for issue,setting,run_setting,issue_id in table:
            agg=lookup[(run_setting,issue_id)]
            sumrow=sr[(issue,setting)]
            gen=agg['generation_errors']
            assert gen==int(sumrow['generation_errors']), (issue,setting,'generation mismatch')
            assert gen<=10
            if gen==0:
                assert not sumrow['tracer_exposed'].strip(),(issue,setting)
                trans='N/A';critic='N/A';status='run-level (no generation error)'
            else:
                seen=agg['tracer_exposed']
                assert seen==int(sumrow['tracer_exposed']),(issue,setting,'tracer mismatch')
                trans=f'{seen}/{gen}'
                strict=agg['strict_from_runs'];partial=agg['partial_from_runs']
                if strict is None:
                    assert agg['unresolved_count']==10 and (setting,issue_id)==('Case 6 / 14B','muon_eta_mismatch')
                    strict=int(sumrow['critique_detected_strict'])
                    partial=int(sumrow['critique_partial'])
                    status='summary-only critique count; exact run mapping unresolved'
                elif not sumrow['critique_detected_strict'].strip():
                    # An extra (non-paper) cutflow row lacked a settled strict count
                    status='supplemental: prior summary leaves strict count unknown'
                else:
                    assert strict==int(sumrow['critique_detected_strict']),(issue,setting,'strict discrepancy')
                    assert partial==int(sumrow['critique_partial']),(issue,setting,'partial discrepancy')
                    status='run-level reproduced'
                critic=(f'{strict}/{gen} correct + {partial}/{gen} partial' if partial else f'{strict}/{gen}')
                if status.startswith('supplemental:'):
                    critic='unknown in original summary (run-level marks 0/5)'
            rec={'issue':issue,'setting':setting,'generation_error':f'{gen}/10',
                'tracer_exposure':trans,'critique_detection':critic,'provenance':status}
            dest.append(rec)
            provenance.append({'issue':issue,'setting':setting,'generation_errors':gen,
                     'tracer_exposed':agg['tracer_exposed'],'unresolved_run_mapping':agg['unresolved_count'],
                     'strict_from_runs':agg['strict_from_runs'] if agg['strict_from_runs'] is not None else '',
                     'strict_from_summary':sumrow['critique_detected_strict'],
                     'provenance':status})
    OUT.mkdir(exist_ok=True,parents=True)
    fields=['issue','setting','generation_error','tracer_exposure','critique_detection','provenance']
    writecsv(OUT/'table16_from_runs.csv',fields,out16)
    writecsv(OUT/'table17_from_runs.csv',fields,out17)
    writecsv(OUT/'supplemental_from_runs.csv',fields,outsupp)
    writecsv(OUT/'comparison_with_summary.csv',list(provenance[0]),provenance)
    writecsv(OUT/'all_21_groups_from_runs.csv', ['setting','issue_id','generation_errors','tracer_exposed','strict_from_runs','partial_from_runs','unresolved_count'],[
        dict(setting=k[0],issue_id=k[1],**v) for k,v in sorted(lookup.items())])
    for n,out in ((16,out16),(17,out17)):
        print(f'Table {n} ({len(out)} rows):')
        for row in out:
            print('  ',row['setting'],row['issue'],row['generation_error'],row['tracer_exposure'],row['critique_detection'],f'[{row["provenance"]}]')
    print('Data:',len(data),'rows;',len(groups),'ten-run groups')
    print('Exception: Case 6 / 14B muon eta Critique 9/10 is summary-only. Exact missed run unresolved.')
    print('Note: supplementary Case 5 / 32B cutflow Critique count remains unknown in the original summary.')
    print('Saved:',OUT)

if __name__=='__main__':main()
