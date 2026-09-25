# artifact-pipeline

## Purpose
Validate build-step dependencies and turn them into one deterministic artifact-pipeline order.

## Key points
- `topologically_order_steps` states its result with closed intrinsics. On success the order is a permutation of the step names (`permutation_by`) and every dependency comes before the step that needs it (`dependency_ordered_by`). `errors complete` makes five conditional errors the whole failure specification, in priority order: blank name, duplicate name, unknown dependency, self-dependency, cycle. Every other input must succeed.
- No formal clause can state the tie-break, so requirement `READY_STEPS_IN_NAME_ORDER` carries it: among the ready steps, the name that is smallest in Unicode code point order comes next. Scenario `ready_steps_in_name_order` checks this on one input where input order, a FIFO Kahn queue and largest-first each produce a different valid order.
- `plan_pipeline` repeats the formal clauses and must take its order from the public `topologically_order_steps` facade (`PLAN_USES_ORDERING_FACADE`). The linked assertion observes that the plan carries the tie-broken order. It does not observe the facade call. The only sign of that call is the nested facade's clause observations recorded during `plan_pipeline` calls.
- Each error scenario makes one condition the first applicable one while every later condition also holds. An implementation that checks the conditions in a different order fails the runtime conditional-error obligation in that scenario.
- Steps keep input order in `List[BuildStep]`. Each step's `needs` is a `Set[Str]`. A blank name is one made only of characters from the fixed 25-character Unicode `White_Space` table, not whatever the target's `strip`/`trim` removes. U+FEFF and U+001C are valid names.

## Evidence
`cott verify` certifies the current snapshot. Semantic coverage records all 14 clauses as `observed` (0 unobserved, 0 unknown, 0 trust declarations). Automatic candidates reach only the success clauses and the blank-name error. The scenarios observe the other four error clauses of each function. `topologically_order_steps` receives those four observations only through its nested facade call inside `plan_pipeline`. `cott requirements` reports both requirements as `observed`. Each rests on one input, which is bounded evidence, not proof. On this snapshot both facades also pass the independent corpus below (3133 cases each).

## Independent acceptance
`check_semantics.py` is an independent permutation oracle for the whole ordering rule, tie-break included. It is not `cott verify`, not a compiler proof and not `semantic_coverage`.

Its scope is finite: every labeled graph on at most 3 nodes, plus explicit larger DAG, Unicode blank-name and error-precedence cases. Where several valid topological orders exist, it expects the lexicographically smallest one.

```bash
.venv/bin/python check_semantics.py --project .
```

The oracle needs compiler-generated, verified output under that interpreter. Both public facades (`topologically_order_steps`, `plan_pipeline`) must match the same corpus.
