# Table 12 — Case 5 (14B), runs 01–10

## Evidence

- Nine uploaded runs (02–10) were directly compared with the previously uploaded run 01.
- All ten `generated_analysis.py` files have an identical SHA-256 hash.
- Tracer outputs fall into two byte-identical variants; their differences involve only ancillary definition-summary explanations (and a cutflow summary entry), not the audited R5/R8/R13/R22 statements.
- The screening CSVs disagree in some primary flags although the underlying generated code and relevant tracer claims are identical. The audit follows the original artifacts, not these inconsistent flags.

## Adjudication proposal

| Issue | Runs 01–10 | Decision | Evidence |
|---|---|---|---|
| R5: `ditau_obj` | 10/10 | Hallucination | Tracer describes a nonexistent named composite at L291–L292. Actual `sum_objects` appears in centrality expression at L311. |
| R8: `dijet_obj` | 10/10 | Hallucination | Tracer describes a nonexistent named composite at L277–L278, which only calculate a scalar mass. |
| R13: b-tag veto chain | 10/10 | Accept E1/E2 as harmless shorthand | Correct caller `n_bjets(event, pt_cut=30, eta_cut=4.7)` at L289; `get_bjets(event)` at L136. |
| R22: ditau/dijet delta phi | 10/10 | Accept E5; implementation mismatch, not tracer mismatch | Source and tracer show `helper_delta_phi(leading_tau['phi'] + subleading_tau['phi'], leading_jet['phi'] + subleading_jet['phi'])` at L309. |

The EXTRA claims identified by the primary model overlap these requirements and must not be counted a second time.

**Effect on Table 12:** The 20 hallucination entries are supported by these two repeated tracer claims. **Do not change the reported 10 dependency errors yet**: without the original aggregation decision ledger, it is unknown whether those counts were attributed to R13 or to a separate/overlapping dependency misstatement for R5/R8. This requires a focused recount with explicit issue IDs, not an assumption.

## Provenance

Generated code SHA-256: `27bc2e676a186060efb3fecb545cc2408367ecc9371ebf55a6f3a9b12a7e9d96` (all ten runs)

Tracer SHA-256 variants:
- `de775d681dd6`: runs 01, 03, 05, 09, 10
- `53d06ef361f7`: runs 02, 04, 06, 07, 08

The `expert_final` column is intentionally blank for newly reviewed runs until human confirmation. Original evaluation CSVs are not modified.
