# artifact-pipeline

## Purpose
Validate build-stage dependencies and turn them into an executable artifact-pipeline order.

## Key points
- `plan_pipeline` calls the generated `curriculum.artifact_pipeline.topologically_order_steps` facade and propagates its ordering error unchanged.
- Pipeline stages keep input order in `List[BuildStep]`; each stage stores its unique dependencies in `Set[Str]`.
- Empty and duplicate stage names are rejected before unknown dependencies, self-dependencies, and cycles. Ready stages are selected lexicographically.

## Independent acceptance
The Cott contract now opts into `errors complete`: normal inputs must succeed, and conditional errors retain their declared priority. Closed predicates check name multiplicities, dependency ordering, and graph errors. Nested-value scenarios exercise a valid chain, a cycle, and overlapping error conditions without public builders. `check_semantics.py` remains an independent permutation oracle for the stronger documented lexicographic tie-break; it is not `cott verify`, not compiler proof, and not `semantic_coverage`.

Scope is finite: every labeled graph on at most 3 nodes, plus explicit larger DAG and error-precedence cases. Ready-node ties are the lexicographically smallest valid topological order.

Blank names use the fixed 25-character Unicode `White_Space` set, not the target's default `strip`/`trim`. In particular U+FEFF and U+001C are valid nonblank names. The independent corpus includes these cross-target boundary cases.

`cott requirements --project . --format json` separates declared `checked_by` links, actual bounded observations and unverified requirements. A passing linked scenario is evidence, not a universal proof of the requirement.

```bash
.venv/bin/python check_semantics.py --project .
```

Requires compiler-generated, verified output under that interpreter. Both public facades (`topologically_order_steps`, `plan_pipeline`) must match the same corpus. `plan_pipeline` must propagate ordering errors unchanged.
