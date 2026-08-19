# artifact-pipeline

## Purpose
Validate build-stage dependencies and turn them into an executable artifact-pipeline order.

## Key points
- Check empty stage names and duplicate names before dependency errors; then distinguish unknown dependencies, self-dependencies, and cycles.
- A topological sort places every stage exactly once by choosing lexicographically the ready stage with no dependencies; failure to place all stages is `Cycle`.
