# contracts-evidence

## Purpose
This dependency-free Cott v0.8 feature project keeps one pure function small enough to inspect its contract and its recorded evidence end to end. After normal emission, run it with:

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

The app calls the generated `curriculum.contracts_evidence.assess_label` facade with a missing label, a short label, and a valid label. It prints the generated `Missing` or payload-carrying `TooShort(actual=...)` error, then the accepted label.

## Composed contract
- `AcceptedLabel(Str)` has `where self.len > 0`. `LabelAssessment` keeps direct `text: Str`, records `length: U64`, and keeps the refined `label: AcceptedLabel`. Its invariants require `text.len == length` and `text == label.value`; canonical construction evaluates both, so a directly constructed result with a stale length or a different refined label fails.
- `assess_label` requires `request.minimum_length > 0` and declares `errors complete`: `Missing` exactly when `request.label` is `Option.Nothing`, then `TooShort` when the offered label is shorter than the minimum, and `Ok` for every other valid request. The success obligation `value.text.len >= request.minimum_length` and the payload obligation `actual.len < request.minimum_length` relate the results to the request. Lengths are `.len`, the Unicode scalar count.
- The `doc` fixes what the clauses leave open: `TooShort.actual` and the accepted `text` are the offered label unchanged. Two scenarios check exactly that: `short_label_reports_offered_text` expects `TooShort(actual: "ok")` for `"ok"` with minimum 3, and `accepted_label_is_reported_unchanged` expects `text == "evidence"`.
- Rule composition (`rule`, `override`, `delete`) is taught in `grammar/assignment-rule`, where the rule is applied to a function. Rule clauses cannot match `Option` payloads or read struct fields, so this project states its failure conditions on the function itself.

## Evidence to inspect
Normal emission creates compiler-owned artifacts. Full verification certifies the artifact snapshot in `generated/generation.json`; the manifest's semantic-coverage policy is a separate gate evaluated from its finalized clause evidence.

| Path | Exact recorded fields | Interpretation |
| --- | --- | --- |
| `.snapshots[.current].verification.limits` | `proof_node_limit`, `proof_branch_limit`, `candidate_limit`, `lifecycle_limit` | The effective non-default budget: `257`, `65`, `17`, and `5`. |
| `.snapshots[.current].verification.contract_proofs` | `algorithm`, `version`, `limits`, `contracts` | Each proof obligation has `kind`, `symbol`, `status`, optional `clauses`, `reason`, and `model`. `status` is the separate static proof result (`proved`, `disproved`, or `unknown`), not an execution claim. |
| `.snapshots[.current].verification.static` | `checker`, `runtime_signatures`, `grade`, `status` | Static signature/type-check capability; its `grade` is `static proof`. |
| `.snapshots[.current].verification.runtime_capability` | `grade`, `sandbox`, `status` | Runtime verification capability; its `grade` is `runtime check`. |
| `.snapshots[.current].verification.contract_tests.contracts[]` | `symbol`, `clause_id`, `span`, `evidence[]` | Every clause keeps distinct test evidence. Each `evidence[]` entry has `grade`, `mode`, `valid_cases`, and `reason`; only exercised valid cases earn `test observation`. A zero-case or unhit conditional clause is `unobserved` with its reason. |
| `.snapshots[.current].verification.contract_tests.scenarios[]` | `scenario_id`, `grade`, `assertions[]` | Scenario runs and the grade of each assertion. |
| `.snapshots[.current].semantic_coverage` | `clauses`, `summary`, `policy` | The semantic-policy result joined from canonical clause inventory and runner evidence, including selected-count, pass/fail, and violations. |

These paths are `jq` selectors: `current` is a digest reference into the record's self-contained
`snapshots` map. For example, run
`jq '.snapshots[.current].semantic_coverage' generated/generation.json`.

`[[verification.coverage.rules]]` selects the `curriculum.contracts_evidence.assess_label` clauses `ensures:2` (success), `error:5` (`Missing`) and `error:6` (`TooShort`); `errors complete` itself is clause 4. It allows neither `unobserved`, `trust declaration`, nor `unknown`, so verification fails unless bounded runner cases or scenarios actually exercise each selected clause.

`trust declaration` is also a possible clause-evidence grade, but this pure `effects []` example in `boundary` mode must not claim it. It is reserved for declarations the verifier intentionally does not execute or prove (for example, effectful work or off-mode optional checks). Do not collapse static proof, runtime check, test observation, unobserved, and trust declaration into one “verified” label. Observations are bounded: they show the exercised cases passed, not that every input does.
