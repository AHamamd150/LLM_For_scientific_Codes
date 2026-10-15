import csv,re,collections,os,json,zipfile, pathlib
import argparse
parser=argparse.ArgumentParser(description='Provisional, note-only issue-family triage of Luna high-priority flags')
parser.add_argument('--input', default='recalculation/table12/results/high_priority_review.csv')
parser.add_argument('--out', default='recalculation/table12/triage')
args=parser.parse_args()
source=args.input
D=pathlib.Path(args.out);D.mkdir(parents=True,exist_ok=True)

def classify(r):
 c=int(r['case']); rid=r['req_id']; n=r['note'].lower(); q=r['requirement_or_claim'].lower(); h=r['hallucination']=='yes'; extra=r['row_type']=='extra_trace_claim'
 def result(group,action,why): return group,action,why
 # specific substantive source/provenance claims first
 if c==2 and 'top_mass_list' in n and ('append' in n or 'populated' in n):
  return result('T01_top_mass_list_false_dependency','targeted','Tracer claims top_mass_list was filled; code allegedly lacks append (Case 2 Run 07).')
 if c==5 and (('ditau_obj' in n and ('no ' in n or 'not ' in n or 'unsupported' in n)) or (('dijet_obj' in n or 'sum_objects' in n) and ('no ' in n or 'not ' in n or 'unsupported' in n))):
  return result('T02_nonexistent_named_composite','targeted','Claimed ditau_obj/dijet_obj or direct sum_objects location may be unsupported; deduplicate EXTRA vs R-level claims.')
 if c==5 and ('n_bjets' in n or 'get_bjets(event)' in n or 'selected jets collection' in n) and (('depend' in n or 'independent' in n or 'consume' in n or 'upstream' in n) or extra):
  return result('T03_bjet_veto_dependency','targeted','Tracer may misstate whether b-jet veto uses independently retrieved versus selected jet collection.')
 if c==5 and ('delta phi' in n or 'phi value' in n or 'phi of' in n or 'constituent phi' in n or 'helper_delta_phi' in n):
  return result('T04_ditau_dijet_phi_provenance','targeted','Check tracer description of observable vs code computing sums of constituent phi.')
 if c==2 and ('closest b-jet' in n or 'closest-b-jet' in n or 'min_dr' in n or 'leading_bjet' in n or 'closest b jet' in n):
  return result('T05_closest_bjet_provenance','targeted','Review distinction: tracer reports actual leading b (E5 acceptable) vs falsely claims closest/minimum; do not treat generation error as tracer error.')
 if c==2 and 'helper_invariant_mass' in n and ('not called' in n or 'fals' in n or 'directly' in n or 'never called' in n):
  return result('T06_false_helper_dependency','targeted','Tracer claims helper call or dependency that code apparently does not use.')
 if c==3 and ('single-constituent' in n or 'single constituent' in n or 'structural label is unsupported' in n or 'structural label is unsupported or misleading' in n):
  return result('T07_wrong_structure_label','targeted','Extra trace may mislabel derived two-photon quantity as single constituent.')
 if c==3 and ('do not exist' in n or 'does not exist' in n or 'nonexistent' in n):
  return result('T08_invalid_source_lines','targeted','Tracer reports non-existent source lines.')
 if c==1 and ('met' in n and ('equality' in n or 'exactly 30' in n or 'equal to 30' in n or 'pt == 30' in n or 'pt < 30' in n)):
  return result('T09_strict_boundary_equality','targeted','Tracer asserts strict > 30 where code may accept equality; check boundary semantics and E1 applicability.')
 # explicitly false claims about histogram coverage/ranges (vs mere omitted plot calls)
 if h and ('range' in n or 'histogram' in n or 'plotting' in n) and ('absent' in n or 'no histogram range' in n or 'no range' in n or 'not specify' in n or 'without a range' in n):
  return result('T10_unsupported_plot_range_claim','targeted','Tracer positively claims plot-range compliance not supported by code, distinct from E3 plot-call omission.')
 if c==1 and ('list comprehension' in n or 'concatenation expression' in n) and ('loop' in n or 'append' in n):
  return result('E1_equivalent_collection_implementation','exception_candidate','Model treats loop vs list-comprehension spelling as error; E1 allows semantic equivalence if resulting collections match.')
 # semantics of bookkeeping: E4 unless code misplacement is claimed -> E5 / separate cross-check
 if ('counter' in n or 'cutflow' in n or 'continue' in n or 'sequential' in n or 'print' in n or 'printing' in n) and ('before their corresponding cuts' in n or 'before the' in n and 'counter' in n or 'premature' in n or 'misplacement' in n or 'mismatched counter' in n or 'duplicated' in n):
  return result('S01_cutflow_implementation_vs_trace','spotcheck','Possible generated-code bookkeeping error (E5) vs false tracer assertion; check representative source.')
 if ('counter' in n or 'cutflow' in n or 'continue' in n or 'sequential' in n or 'print' in n or 'printing' in n) and ('trac' in n or 'omit' in n or 'cites' in n or 'source' in n):
  return result('E4_cutflow_and_output_bookkeeping','exception_candidate','Missing control-flow/print granularity, generally E4 candidate; preserve independent cut-boundary semantics for E6.')
 # histogram calls/config, omitted details, known code mismatch E5
 if ('histogram' in n or 'plt.hist' in n or 'plot call' in n or 'plotting' in n or 'plot_hist' in n or 'png' in n or 'label' in n or 'filename' in n or 'range argument' in n or 'savefig' in n or 'plot operation' in n or 'plot at' in n) and not h:
  return result('E3_plot_call_or_format_omission','exception_candidate','Plot science value/provenance traced but plot call/config absent per Luna; E3 candidate subject to quantity/provenance check.')
 if c==3 and ('counter' in n or 'cutflow' in n or 'continue' in n):
  return result('E4_cutflow_and_output_bookkeeping','exception_candidate','Cutflow granularity, separate from E6.')
 if c==5 and ('helper' in n or 'collection' in n) and ('dependency' in n or 'upstream' in n):
  return result('S02_other_dependency_provenance','spotcheck','Other dependency issue requiring sample code verification.')
 if ('helper' in n or 'source' in n or 'dependency' in n or 'provenance' in n) and not h:
  return result('S02_other_dependency_provenance','spotcheck','Provenance/dependency uncertain from model note; compare one code/tracer pair.')
 return result('S03_unclassified_review','spotcheck','Not confidently assignable from the pre-annotation text; inspect evidence before changing priority.')

with open(source,newline='',encoding='utf-8-sig') as f: records=list(csv.DictReader(f))
for r in records:
 gr,act,why=classify(r)
 r['triage_group']=gr;r['provisional_action']=act;r['triage_reason']=why;r['expert_checked']='NO';r['human_review_status']='not_reviewed'

basefields=list(records[0].keys())
with (D/'all_240_triaged.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=basefields);w.writeheader();w.writerows(records)
q=[r for r in records if r['provisional_action']!='exception_candidate']
with (D/'targeted_and_spotcheck_queue.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=basefields);w.writeheader();w.writerows(q)

s=collections.defaultdict(list)
for r in records:s[r['triage_group']].append(r)
group_rows=[]
for group,rr in sorted(s.items()):
 one=rr[0]; case_runs=sorted(set((int(r['case']),int(r['run'])) for r in rr))
 row={'triage_group':group,'provisional_action':one['provisional_action'],'rows':len(rr),'case_runs':len(case_runs),'cases':','.join(map(str,sorted(set(c for c,_ in case_runs)))),'example_case':one['case'],'example_run':one['run'],'example_req_id':one['req_id'],'triage_reason':one['triage_reason'],'example_model_note':one['note'],'review_status':'not_reviewed'}
 group_rows.append(row)
with (D/'issue_groups.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(group_rows[0]));w.writeheader();w.writerows(group_rows)
with (D/'review_examples_by_group.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['triage_group','case','run','row_type','req_id','requirement_or_claim','note','code_path','tracer_path','expert_review_result','expert_comment']);w.writeheader();
 for g in group_rows:
  subs=s[g['triage_group']]
  seen=set();sel=[]
  for r in subs:
   k=(r['case'],r['run'])
   if k not in seen: sel.append(r);seen.add(k)
   if len(sel)>=2:break
  for r in sel:w.writerow({**{k:r.get(k,'') for k in w.fieldnames},'triage_group':g['triage_group'],'expert_review_result':'','expert_comment':''})
print('total',len(records),'groups',len(s),'actions',collections.Counter(r['provisional_action'] for r in records))
for gr in group_rows: print(gr['triage_group'],gr['rows'],gr['case_runs'])
print('files',list(D.iterdir()))
