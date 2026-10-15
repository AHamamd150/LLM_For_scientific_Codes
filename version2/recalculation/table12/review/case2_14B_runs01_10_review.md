# Case 2 / Qwen3-14B: tracer review of 10 frozen runs

**Status:** source-code / tracer-assisted screening. Final expert decisions are blank; the original primary-evaluation CSVs and original runs have not been modified. **Do not treat the proposed classification as human adjudication until reviewed.**

## Sources and scope

- Source: `paper_data/runs/14B/frozen_timing/run_01` through `run_10`, `case2/execution/generated_analysis.py` and `case2/critique/tracer/final_output.txt`.
- Original pre-screening: `paper_data/tracer_evaluation/14B/case2_run01.csv` through `case2_run10.csv`.
- **238 requirement rows plus 2 extra-trace-claim rows** (in Run 09). Five byte-distinct code variants; eight byte-distinct tracer versions. SHA-256 provenance hashes and exact source paths are in the CSV.
- The 240-row review CSV preserves the primary classifications and notes verbatim and adds *proposed* review actions; the focused queue has 20 rows. Routine rows without primary flags were not independently reviewed item by item.
- No LLM API calls, physics workflow reruns, or modification of source CSVs occurred.

## Findings

### 1. Run 07 / R16 — confirmed tracer hallucination (1 item)

Generated code computes `top_mass` (around L356), but does **not** append it to `top_mass_list`. Nevertheless the tracer **definition summary** reports `top_mass_list.append(top_mass)` (tracer L202), an operation absent from the program. The histogram consumes the empty list (code L422). This is a factual invention of a code dependency, not an error of the generator merely differing from the specification. **Proposed count: hallucination 1**. This reproduces the review of Run 07 discussed earlier.

Run 07 / R17 is different: code L363–L368 and tracer L19, L135–L137 both preserve the `min_dr` dependence, hence it is **not** a tracer dependency error under E1/E3.

### 2. Run 10 / R12–R21 — 10 candidate coverage misses: E3 decision needed

The tracer's **SPEC BULLET ANALYSIS** ends after the hadronic top construction (tracer L12) and entirely omits the ten validation-plot bullet mappings. The generated code nonetheless contains all ten histograms (around code L380–L449). The **DEFINITION SUMMARY** (tracer L48–L129) identifies multiple underlying observables and their dependencies (e.g. `mt`, `met`, `top_mass`, `ht`). The open question is whether generic summary entries that do not trace the plot's *actual output data* satisfy E3's requirement to identify the scientific quantity and its provenance.

- **If plot-item coverage requires explicit linkage from requested plot to the implemented histogram quantity**, all ten are legitimate coverage misses, consistent with the current Table 12.
- **If isolated quantities in the definition summary alone are accepted as tracing each requested plot**, at least some of the ten would be forgiven under E3, and Table 12 must be reconsidered.

Because a quantity can be calculated in code yet never added to a histogram (as demonstrated by Run 07), these are not equivalent criteria. **Request one explicit expert policy decision** before finalizing the 10-item count. Plotting calls, labels, file names and bin counts are *not* required under E3; the issue is coverage of the plotted data path itself.

### 3. Runs 01, 09, 10 — invariant-mass function attribution (8 rows including duplicate)

In the event loops, code reads reconstructed-composite mass fields directly, e.g. `w_hadronic['mass']` (L341) and `top_candidate['mass']` (L352). In the corresponding SPEC bullets, the tracer instead labels the mass dependency as `helper_invariant_mass(...)`. The defined helper (L89–L92) computes a mathematically equivalent invariant mass, but that helper was **not actually called in these event loops**.

The scientific quantity and its input constituents agree, but the literal function-call provenance does not. **Proposed E1 accept as an immaterial equivalent mathematical description**, *conditional on expert agreement*; otherwise these require a stricter source-attribution score. Run 09 `EXTRA1` duplicates the same point and must not be counted again.

### 4. Run 01 / R18 — closest b-jet min-dependency (1 row)

Code L361–L366 loops over selected b jets, updating `min_dr`. The tracer's SPEC bullet L19 says `helper_delta_r(lepton,bjet) -> dr -> dr_lepton_bjet_list`, without the minimum reduction. Unlike Run 07, the min operation is not obvious from this bullet. This is a **possible provenance loss**. We recommend expert inspection; it should not be automatically waived as an omitted `plt.hist` call under E3.

### 5. E3/E4/E5 exclusions in other runs

- Plot bullets that identify the computed value and data list but omit `plt.hist`, `savefig` or plot formatting: **proposed E3**, not a source error merely because Luna expected a plotting line.
- Cutflow sequencing, `continue` and printing details: **proposed E4** when the scientific selection is identified. Selection-boundary semantics are separately handled under E6.
- In several runs the generator incorrectly plots ΔR to the **leading** instead of the **closest** b jet. The tracer explicitly writes `helper_delta_r(lepton, leading_bjet)` in the computed-as field. The task-card bullet heading retains the word *closest*, but this is a **generator–specification mismatch** (E5), not a tracer hallucination. Run 09 `EXTRA2` is likewise not an additional actual tracer claim.
- For HT, tracer identifies `scalar_pt_sum(selected_jets)`, consistent with the implementation even if the task card said *all jets* (E5).

## Provisional counts and reviewer action

| Category | Run(s) | Requirement-level items | Status |
|---|---|---:|---|
| Tracer hallucination, `top_mass_list.append` | 07 | 1 | Confirmed by code/tracer comparison; awaiting record of expert acceptance |
| Missing plot-bullet mappings | 10 | 10 | Coverage candidates; **expert decision on E3** |
| Mass helper attribution shorthand | 01, 09, 10 | 7 requirements + 1 duplicate extra claim | Proposed E1 exception; **expert decision** |
| Missing minimum operation in tracer chain | 01 | 1 | **Expert check** |

All other primary adverse labels were screened as potential E1/E3/E4/E5 exceptions, **not exhaustively human-validated**. A single high-level decision for each of the three unresolved patterns is more useful than asking a human to review all 240 rows.

The existing Table 12 reports Case 2 as 1 hallucination and 10 coverage misses in 2 affected runs. **That agrees with this audit if and only if the Run 10 coverage criterion above is endorsed and the two attribution cases are accepted under E1.** The review does not force agreement with those published numbers.

## Files

- `case2_14B_runs01_10_review.csv`: all 240 rows; original Luna values preserved; proposed actions and evidence added.
- `case2_14B_review_queue.csv`: 20 specifically identified source/policy decision rows.
- `case2_14B_run_summary.csv`: counts by run and SHA-256 IDs.

When the expert confirms a policy decision, record it in a new review record or in the blank `human_review` and `expert_final` columns of the **new review CSV**, not in any historical evaluation CSV.
