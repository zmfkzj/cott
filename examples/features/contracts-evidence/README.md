# contracts-evidence

## Purpose
This dependency-free Cott v0.8 feature project keeps one pure, manifest-bound function small enough to inspect end to end. After normal emission, run it with:

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

The app calls the generated `curriculum.contracts_evidence.assess_label` facade with a missing label, a short label, and a valid label. It prints the generated `Missing` or payload-carrying `TooShort(actual=...)` error, then the accepted label.

## Composed contract
- `AcceptedLabel(Str)` has `where self.len > 0`. `LabelAssessment` retains direct `text: Str`, records `length: U64`, and retains the refined `label: AcceptedLabel`. Its invariants require `text.len == length` and `text == label.value`; canonical construction evaluates both, so a directly constructed result with a stale length or different refined label fails.
- `BaselineLabelRule` initially permits `Legacy` and `Missing`. `RefinedLabelRule` overrides `Missing` with a false conditional obligation and deletes `Legacy`, demonstrating standalone rule override/delete without requiring a rule-level result payload type.
- `assess_label` returns `Result[LabelAssessment, LabelEvidenceError]`, explicitly declares `Missing`, and adds the request-specific clauses: `request.minimum_length > 0`, the successful-result length relation, and the conditional `Option.Some(text)` error obligation. Its nested `Result.Err(LabelEvidenceError.TooShort(actual))` guard records the payload relation `actual.len < request.minimum_length`.
- The immutable field paths `value.text` and `request.minimum_length`, with `.len` comparisons, are supported proof-v2 difference constraints. The binding imports staged generated types and returns only `Ok(LabelAssessment(text=label, length=len(label), label=AcceptedLabel(value=label)))` or the declared `Err` variants; it does not bypass the public facade or fabricate verification output.

## Evidence to inspect
Normal emission creates compiler-owned artifacts. Full verification certifies the artifact snapshot in `generated/generation.json`; the manifest's semantic-coverage policy is a separate gate evaluated from its finalized clause evidence.

| Path | Exact recorded fields | Interpretation |
| --- | --- | --- |
| `current.verification.limits` | `proof_node_limit`, `proof_branch_limit`, `candidate_limit`, `lifecycle_limit` | The effective non-default budget: `257`, `65`, `17`, and `5`. |
| `current.verification.contract_proofs` | `algorithm`, `version`, `limits`, `contracts` | Each proof obligation has `kind`, `symbol`, `status`, optional `clauses`, `reason`, and `model`. `status` is the separate static proof result (`proved`, `disproved`, or `unknown`), not an execution claim. |
| `current.verification.static` | `checker`, `runtime_signatures`, `grade`, `status` | Static signature/type-check capability; its `grade` is `static proof`. |
| `current.verification.runtime_capability` | `grade`, `sandbox`, `status` | Runtime verification capability; its `grade` is `runtime check`. |
| `current.verification.contract_tests.contracts[]` | `symbol`, `clause_id`, `span`, `evidence[]` | Every clause keeps distinct test evidence. Each `evidence[]` entry has `grade`, `mode`, `valid_cases`, and `reason`; only exercised valid cases earn `test observation`. A zero-case or unhit conditional clause is `unobserved` with its reason. |
| `current.semantic_coverage` | `clauses`, `summary`, `policy` | The semantic-policy result joined from canonical clause inventory and runner evidence, including selected-count, pass/fail, and violations. |

`[[verification.coverage.rules]]` selects the real `curriculum.contracts_evidence.assess_label` clauses `ensures:2` and `error:5`. It allows neither `unobserved`, `trust declaration`, nor `unknown`; the valid, missing, short, and successful facade cases make the selected success and conditional-error obligations meaningful coverage targets.

`trust declaration` is also a possible clause-evidence grade, but this pure `effects []` example in `boundary` mode must not claim it. It is reserved for declarations the verifier intentionally does not execute or prove (for example, effectful work or off-mode optional checks). Do not collapse static proof, runtime check, test observation, unobserved, and trust declaration into one “verified” label.
