# Helper-selection stability

- Run root: `frozen_timing`
- Source: `selection`
- Runs discovered: 10
- Cases discovered: 1, 2, 3, 4, 5

Jaccard similarity is defined as $J(A,B)=|A\cap B|/|A\cup B|$.

| Case | Runs | Common | Non-common | Min/run | Max/run | Mean helpers/run | Mean Jaccard | SD Jaccard | Jaccard range |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 22 | 0 | 22 | 22 | 22.000 | 1.000 | 0.000 | 1.000–1.000 |
| 2 | 10 | 20 | 2 | 20 | 22 | 21.000 | 0.949 | 0.046 | 0.909–1.000 |
| 3 | 10 | 14 | 0 | 14 | 14 | 14.000 | 1.000 | 0.000 | 1.000–1.000 |
| 4 | 10 | 17 | 3 | 18 | 19 | 18.900 | 0.970 | 0.061 | 0.850–1.000 |
| 5 | 10 | 16 | 0 | 16 | 16 | 16.000 | 1.000 | 0.000 | 1.000–1.000 |

## Definitions

- **Common**: helpers present in every analyzed run for the case.
- **Non-common**: helpers present in at least one but not all analyzed runs.
- **Mean Jaccard**: mean over all unordered run pairs within the same case.
- **SD Jaccard**: sample standard deviation over the pairwise Jaccard values.

The metric quantifies set stability only; it does not measure helper relevance or correctness.

The default source, `helpers/selection.json`, is the workflow's normalized, dependency-expanded selector output. Domain default helpers added later when constructing the generation card are not included unless they are present in `selection.json` itself.

To summarize the actual helper list passed to code generation instead, run:

```bash
python3 summarize_helper_selection.py frozen_timing --source generation
```
