# Case 1 / Qwen3-14B: tracer audit across 10 runs

**Status:** Model-assisted independent review; human adjudication is pending. The original `paper_data/tracer_evaluation/14B/case1_run*.csv` and the generated programs/traces are unchanged. Source paths in the CSV are relative to the workbench root.

## Provenance and scope

- 10 run bundles, 247 task-card requirement rows, 4 extra-trace-claim rows (251 total).
- Byte-identical generated programs: runs 01,05,08,09,10; and runs 02,03,04,06,07 (two source-code variants).
- Byte-identical tracer outputs: runs 03,04,06,07, and 09,10; other runs are distinct (six trace variants).
- No new LLM inference or scientific workflow execution was performed for this audit.
- `case1_14B_runs01_10_review.csv` includes all primary rows, with *provisional* rule/action and separate blank `human_review` and `expert_final` columns.
- `case1_14B_review_queue.csv` contains only items needing an explicit human policy decision (not all rows that carried a Luna primary flag).

## Review findings

**E3 / plots:** The source and provenance of histogram arrays are reported even where the tracer omits `plt.hist`, binning, plotting details, or `savefig`. These are *suggested* E3 exceptions, not measured semantic errors.

**E4 / cutflow and output bookkeeping:** Omitted `print`, CSV write statements, and summary control-flow details are proposed E4 exceptions if the relevant scientific variables and selections are traceable.

**E1 / equivalent selection wording:** The tracer often uses schematic list-comprehension notation for an explicit Python loop with `append`, including in the `EXTRA` claims; in the inspected code the selected collections and numerical thresholds match. The run 01 `bjets` definition summary also uses a fictitious *filtered bjets collection*, although the real code calls `get_bjets(event)` then applies the same pT/eta veto through `any(...)`. This is proposed as an E1 equivalence for the veto's effective selection (not a literal source reconstruction).

**E2 / helper expansion:** Run 06's b-jet veto follows the caller `n_bjets(event,30,2.5)`. The helper-side pT/eta implementation need not be reproduced recursively.

### Requires human decision: MET boundary

The generated code in both variants rejects events with `met['pt'] < 30`; therefore the *effective implementation* accepts `met['pt'] >= 30`. In runs **01,02,03,04,06,07,09,10**, the tracer instead summarizes the selection as `met['pt'] > 30`. This is an **exact strict-versus-inclusive boundary discrepancy**. Runs **05 and 08** quote the actual rejection condition and do not exhibit that tracer-summary discrepancy. The extra claim in run 10 (`EXTRA3`) repeats the same issue and must not be counted a second time.

This may be considered an immaterial boundary shorthand in numerical collider analyses, but strict mathematical equivalence does **not** hold. It must not be silently waived as E1. Decide whether to (a) accept it explicitly under an operational interpretation and mention the exception, or (b) record it as a tracer boundary-semantics mismatch. Since the manuscript evaluates selection/rejection control flow separately under E6, specify whether the discrepancy belongs to the E6 assessment rather than automatically counting it in the E1–E5 Table 12.

### Separate implementation observation (not a tracer-fidelity score)

One code variant checks `len(leptons) != 1` before its `Electron and muon selection` cutflow label and then repeats exactly-one-lepton check; the other variant uses an unconditional collection-definition counter followed by the lepton selection. This may affect cutflow semantics, but was not counted as a tracer error under E4/E5. The paper's cutflow assessment should be considered separately.

## Tentative conclusion

Apart from the MET exact-boundary question, the flagged issues inspected here have plausible E1–E4 exceptions. **Do not finalize a zero-error Case 1 count until the human reviewer chooses the boundary treatment.** The review is intentionally not back-fitted to the manuscript's existing Table 12.
