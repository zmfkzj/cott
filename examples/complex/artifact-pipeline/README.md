# artifact-pipeline

## Purpose
Validate build-stage dependencies and turn them into an executable artifact-pipeline order.

## Key points
- `plan_pipeline` calls the generated `curriculum.artifact_pipeline.topologically_order_steps` facade and propagates its ordering error unchanged.
- Pipeline stages keep input order in `List[BuildStep]`; each stage stores its unique dependencies in `Set[Str]`.
- Empty and duplicate stage names are rejected before unknown dependencies, self-dependencies, and cycles. Ready stages are selected lexicographically.

## Independent acceptance
`check_semantics.py` is an executable corpus with its own permutation oracle. The Cott DSL cannot state graph-valued scenario inputs or universal graph conditions, so this script is the acceptance check. It is not `cott verify`, not compiler proof, and not `semantic_coverage`.

Scope is finite: every labeled graph on at most 3 nodes, plus explicit larger DAG and error-precedence cases. Ready-node ties are the lexicographically smallest valid topological order.

```bash
.venv/bin/python check_semantics.py --project .
```

Requires compiler-generated, verified output under that interpreter. Both public facades (`topologically_order_steps`, `plan_pipeline`) must match the same corpus. `plan_pipeline` must propagate ordering errors unchanged.
