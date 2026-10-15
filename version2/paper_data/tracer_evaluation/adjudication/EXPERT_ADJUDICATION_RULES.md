# Expert adjudication rules for tracer evaluation

These rules define cases that are not treated as tracer errors during expert adjudication.

- **E1** — Semantically equivalent descriptions of the implemented computation are accepted; literal reproduction of the source code is not required.
- **E2** — The caller-side helper call is sufficient. Recursive expansion of helpers called inside that helper is not required.
- **E3** — For plotted quantities, identifying the scientific quantity and its provenance is sufficient; citation of the plotting call or plotting configuration itself is not required.
- **E4** — The tracer is not penalized when the required source location or tracing granularity is not uniquely specified, including cutflow ordering, printing, and similar bookkeeping.
- **E5** — A mismatch between the task card and the generated code is not itself a tracer error; the generated code is treated as the ground truth for what was actually implemented.

The `pre_adjudication_note` column is model-generated assistance only. The `expert_final` column is intentionally left blank for HEP-expert review. Candidate real tracer errors are explicitly marked as requiring expert review.
