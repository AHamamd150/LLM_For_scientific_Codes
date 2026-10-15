# Architecture and migration notes

```text
card + generated code
        |
        v
      tracer   ──> AS-IMPLEMENTED SPEC + definition trace
        |
        v
     critique  ──> raw findings ──> heuristic review filter
```

Both stages depend only on the `ChatProvider` interface. Hugging Face routing is
an adapter and can later be replaced without changing the pipeline.

The continuation merge, incomplete-entry repair, duplicate-summary handling,
definition-summary parser, critique repair, deduplication, and finding filter
from the experimental code are retained as core behavior.

The experimental `explain` stage is publicly named `tracer`. Its purpose and
output structure are unchanged; the Critique prompt refers to `TRACER OUTPUT`.

Excluded from the public component:

- model-matrix shell scripts;
- warm-up and retry scripts;
- `output_run1/` and `output_run2/`;
- generated target programs used for the paper comparison.

These are experiment assets rather than library behavior.

The original card and generated code are never modified. The common workflow
may use the critique report to create a later card or code revision, but that
decision lies outside this package.
