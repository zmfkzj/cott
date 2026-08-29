# artifact-pipeline

## Purpose
Validate build-stage dependencies and turn them into an executable artifact-pipeline order.

## Key points
- `plan_pipeline` calls the generated `curriculum.artifact_pipeline.topologically_order_steps` facade and propagates its ordering error unchanged.
- Pipeline stages keep input order in `List[BuildStep]`; each stage stores its unique dependencies in `Set[Str]`.
- Empty and duplicate stage names are rejected before unknown dependencies, self-dependencies, and cycles. Ready stages are selected lexicographically.
