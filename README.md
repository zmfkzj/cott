# cott

`cott` is a Rust compiler for a declaration- and contract-first DSL. A bodyless `.cott` module
declares public types, functions, contracts, and errors: declarative intent is the agent's input,
target projection is second, and verification reports only the evidence it obtained. Cott is not a
general-purpose execution language; Cott functions have no executable bodies.

`architecture.md` is the normative v0.1 contract.

## Declaration-first contract

Every declaration is resolved and type-checked, lowered to Canonical IR v3, projected to the target,
and then checked using the available capabilities. An unavailable implementation, runtime check, test
input, or safe execution permission lowers evidence rather than rejecting an otherwise valid
declaration. Syntax, names, generic arity, constants, Opaque tags, and hash-key admissibility remain
hard errors.

`Any` and `Unknown` are explicit prelude types, not omitted annotations. `Any` means intentionally
unconstrained; `Unknown` requires narrowing or target-side adaptation. `Iterator[T]` has one type
argument. `Generator[Y, S, R]` has yielded, sent, and completion types; constructing either lazy
value is not evidence that its lifecycle or declared effects occurred.

`Opaque["tag"]` preserves a tagged foreign identity. Its tag matches
`[a-z][a-z0-9._-]{0,63}`; it may occur recursively in aliases, newtypes, fields, enum payloads,
traits, containers, and function or method signatures, including agent implementations. It is
forbidden only as a compile-time constant or hash key.

External types use exactly this syntax:

```cott
external type Name
```

An external declaration identifies a semantic Cott type; it contains neither a backend nor a source
path. Each backend joins the fully qualified Cott external symbol to its own manifest projection
table. Python uses `[target.python.external_types]`, with a quoted fully qualified Cott symbol as the
key and a `module:Qualname` value:

```toml
[target.python.external_types]
"example.http.Request" = "starlette.requests:Request"
```

Every external declaration must have exactly one valid Python projection for Python emission; missing,
stale, non-external, or malformed mappings fail emission. The mapping never enters Canonical IR or
implementation selection. References remain named Cott types, so a projected Python object may cross a
contract boundary without an adapter; an adapter is needed only when an external API's call contract
must be changed. A Python binding is optional implementation selection, not contract source: an absent
binding leaves an eligible function unresolved for an agent; a present binding must resolve and have a
compatible signature. Agents receive the resolved contract and a separate deterministic Python
projection section; they may implement eligible unresolved signatures containing `Any`, `Unknown`,
external, lazy, or recursively placed `Opaque` types, but cannot weaken a declaration or add a Cott
body. Future Rust and TypeScript backends can provide corresponding projection tables, but neither
target nor its table is implemented today.

Function contracts use a closed, pure, typed expression grammar: literals, names, constants, enum
values, fields, `.len`, declared `old(self.field)`, arithmetic, comparisons, and boolean operators.
They never execute arbitrary calls, indexing, collection literals, reflection, or Python source.
Target-side external projection inspection, when configured, runs only under containment rules and
records evidence; it never changes declaration validity or Canonical IR.

| Cott | Python ABI projection |
| --- | --- |
| `Any` | `typing.Any` |
| `Unknown` | `object` |
| `Iterator[T]` | `typing.Iterator[T]` |
| `Generator[Y, S, R]` | `typing.Generator[Y, S, R]` |
| `Factory[Concrete]` | exact generated `type[Concrete]` class object |
| `Opaque["tag"]` | `cott_runtime.Opaque[typing.Literal["tag"]]` |
| `external type Name` | `[target.python.external_types]` joins its fully qualified Cott symbol to a Python `module:Qualname` |

Canonical IR schema version **3** represents `Any` as `{"kind":"any"}`,
`Unknown` as `{"kind":"unknown"}`, iterators as `{"kind":"iterator","item":...}`, generators as
`{"kind":"generator","yield":...,"send":...,"return":...}`, and Factory as
`{"instance":{"kind":"named",...},"kind":"factory"}` (lexical key order: `instance`, `kind`).
`factory.instance` is the resolved named impl type. An `external_type` declaration contains only
semantic declaration metadata (`annotations`, `doc`, `kind`, `name`, `public`, `source_order`, and
`span`); bindings, projection mappings, locations, hashes, and target tool identities are
provenance/configuration inputs, not replacements for this semantic form.

`Factory[Concrete]` has exactly one argument. Aliases resolve first; the result must be an argument-free
named impl declaration. It has no value literal, is neither hash-stable nor admissible as impl state,
and contract tests never synthesize it. Python projects it to the exact generated `type[Concrete]`
class object: no instance, subclass, or arbitrary callable is valid, and validation never invokes it.
The class's compiler-generated init supplies the callable signature. A cross-module Python annotation
imports `Concrete` from its public Cott facade, never from a `_types` module.

Verification reports capability-based evidence per symbol and clause:

| Evidence | Meaning |
| --- | --- |
| static proof | A deterministic non-executing declaration, signature, type, or target-shape check passed. |
| runtime check | A configured production boundary actually executed the check. |
| test observation | A permitted valid case actually ran and observed the contract point. |
| unobserved | No valid permitted runtime or test observation was available. |
| trust declaration | The declaration is accepted but not generally proven by Cott. |

Generated and selected artifacts record contract and implementation hashes, source/runtime and target
identities, and validation mode. Provenance establishes observed identities, never unobserved behavior
or execution.

## Generation-first curriculum

The maintained curriculum has 42 projects:

1. **Grammar — 10 projects:** learn declarations, types, refinements, and focused contracts.
2. **Simple — 16 projects:** generate a reusable leaf and a domain-named final operation that calls
   the leaf through its generated facade.
3. **Complex — 16 projects:** generate meaningful validation, transformation, and aggregation
   stages that compose through generated facades.

`grammar/checked-add` is the only manifest-binding lesson. The other 41 curriculum projects have no
`[target.python.implementations]` table or `python/cott_bindings/` source. Their committed
`python/_cott_impl/` implementations and `generated/` trees are outputs created by `cott generate`
and retained so the generated code and provenance can be inspected directly.

The commands below use an installed `cott` binary and run from the repository root. In a source
checkout, `cargo run --` can replace `cott`. Each example's Python environment can be provisioned
with:

```bash
UV_PROJECT_ENVIRONMENT=examples/<level>/<project>/.venv \
  uv sync --project examples/<level>/<project>/python
```

## The one binding lesson: `checked-add`

`checked-add` exposes one function:

```text
checked_add(left: I32, right: I32) -> I64
```

It alone demonstrates how a manifest symbol maps to authored Python:

```text
examples/grammar/checked-add/
├── cott.toml
├── src/curriculum/checked_add.cott
└── python/
    ├── pyproject.toml
    └── cott_bindings/curriculum/checked_add/
        └── checked_add.py
```

```toml
[target.python.implementations]
"curriculum.checked_add.checked_add" = "cott_bindings.curriculum.checked_add.checked_add:checked_add"
```

The optional mapping selects this existing compatible implementation; it does not define the Cott
contract. Its key and target must resolve and its signature must be compatible. Emission verifies the
selected source, copies it to the canonical runtime location
`generated/python/_cott_impl/curriculum/checked_add/checked_add.py`, and publishes the facade at
`generated/python/curriculum/checked_add.py`.

```bash
project=examples/grammar/checked-add
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from curriculum.checked_add import checked_add; print(checked_add(2, 3))'
# 5
```

This is the only curriculum project with an authored `cott_bindings` tree or implementation mapping.

## Generate every other example from `.cott`

The repository retains each successful generation result:

```text
examples/<level>/<project>/
├── cott.toml
├── src/curriculum/<module>.cott
├── python/
│   ├── pyproject.toml
│   └── _cott_impl/<exact Cott module path>/<function>.py
└── generated/
```

Use the same generation-first sequence for every project except `checked-add`:

```bash
cott check --project examples/<level>/<project>
cott fmt --check --project examples/<level>/<project>
cott emit python --project examples/<level>/<project>
cott generate --agent omp --target python --project examples/<level>/<project>
cott verify --project examples/<level>/<project>
```

This sequence is idempotent on the committed examples: `generate` invokes an agent only for eligible
functions still listed in `current.unresolved`; already accepted durable implementations are reused.

`cott emit python` is a planning step. It never invokes an agent: it emits compiler-owned metadata,
records every eligible missing function in `current.unresolved`, and omits unresolved functions from
the public facade. A successful emit is therefore not yet a deployable result.

`cott generate --agent omp --target python` runs one function-scoped agent process for each eligible
unresolved public function. Accepted implementations become durable source at:

```text
python/_cott_impl/<exact Cott module path>/<function>.py
```

Those files are created by `cott generate`, not handwritten as bindings, and are committed here for
inspection. They survive later emission. The compiler also publishes checked public modules below
`generated/python/`. `cott verify` is the full-project gate and succeeds only after every required
function has an accepted implementation.

Composition does not bypass contracts. If a generated final function calls a generated helper, it
imports the helper from the exact public Cott facade:

```python
from curriculum.alphabetical_file_groups import classify_filename
```

Generated code must not import another implementation file or `_cott_impl` directly. Crossing the
facade keeps helper provenance, ABI validation, `requires`, `ensures`, and declared errors active at
every edge.

### Generated grammar leaf

`module-export-snapshot` declares the leaf `build_snapshot` in
`src/curriculum/module_export_snapshot.cott`; its accepted generated implementation is retained next
to the contract.

```bash
project=examples/grammar/module-export-snapshot
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # refreshes output; the durable implementation stays resolved
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from curriculum.module_export_snapshot import build_snapshot; print(build_snapshot(7, 11))'
```

Generation creates
`python/_cott_impl/curriculum/module_export_snapshot/build_snapshot.py`; the application calls only
`curriculum.module_export_snapshot.build_snapshot`.

### Generated simple composition

`alphabetical-file-groups` declares a one-file classifier and a collection operation:

```text
group_filenames → classify_filename
```

Its checkout retains one generated `_cott_impl` file per function. The generated
`group_filenames` implementation calls `classify_filename` through
`curriculum.alphabetical_file_groups`.

```bash
project=examples/simple/alphabetical-file-groups
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # refreshes output; both implementations stay resolved
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from cott_runtime import CottList; from curriculum.alphabetical_file_groups import group_filenames; print(group_filenames(CottList(values=["apple.txt", "Ryan.py", "010.txt", "!note"])))'
```

The final operation preserves input order, invokes the checked leaf facade for each item, and
propagates the first declared error unchanged.

### Generated complex module

`page-build` declares three stages:

```text
build_page → render_page_html → escape_page_text
```

Generation produced and retained three durable files below
`python/_cott_impl/curriculum/page_build/`; the generated intermediate and final implementations
import their dependencies from `curriculum.page_build`.

```bash
project=examples/complex/page-build
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # refreshes output; all three implementations stay resolved
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  "from curriculum.page_build_types import PageSource; from curriculum.page_build import build_page; print(build_page(PageSource(slug='hello-world', title='Hi & Bye', body='first\nsecond')))"
```

`build_page` owns request validation, `render_page_html` owns document assembly, and
`escape_page_text` owns escaping. Both composition edges still traverse generated contract facades.

### FastAPI integration

`examples/integrations/fastapi-hello` adapts FastAPI's official
[First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) `GET /` example. Cott declares
the typed `HelloResponse` and generates `read_root`; the four-line `python/app.py` adapter only
registers that checked facade with FastAPI.

```bash
project=examples/integrations/fastapi-hello
UV_PROJECT_ENVIRONMENT="$project/.venv" UV_PYTHON=3.14.6 uv sync --project "$project/python"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/fastapi" dev "$project/python/app.py"
curl http://127.0.0.1:8000/
# {"message":"Hello World"}
```
### Modular multi-file generation

`examples/modular/order-management` demonstrates code generation across multiple `.cott` source modules:

```text
store.order.calculate_order → store.order.validate_line
                            ↘ store.catalog.find_item
```

1. `src/store/catalog.cott` declares the catalog domain (`Item`, `Catalog`, `CatalogError`, and `find_item`).
2. `src/store/order.cott` imports catalog types (`use store.catalog.{Catalog, CatalogError, Item}`) and declares order operations (`Order`, `OrderReceipt`, `OrderError`, `validate_line`, and `calculate_order`).
3. The generated `calculate_order` implementation imports `validate_line` from `store.order` and `find_item` from `store.catalog`, crossing generated contract facades cleanly.

```bash
project=examples/modular/order-management
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" python3 "$project/python/app.py"
```

## Complete project index

The graph notation points from a caller to the public helper facade it invokes. `leaf` means the
final symbol is the project's only public function. Except for `checked-add`, every function in
these graphs is generated from the project's `.cott` declarations.

### Grammar — 10 projects

| Project | Final symbol | Public helper graph |
| --- | --- | --- |
| `assignment-rule` | `parse_assignment` | leaf |
| `checked-add` | `checked_add` | leaf |
| `cta-row` | `decode_row` | leaf |
| `fractional-range-values` | `build_bounded_range` | leaf |
| `module-export-snapshot` | `build_snapshot` | leaf |
| `parse-assignment` | `parse_assignment` | leaf |
| `portfolio-cost` | `calculate_portfolio_cost` | leaf |
| `stock-input-validation` | `validate_stock_input` | leaf |
| `validated-stock` | `value_stock` | leaf |
| `stock-record` | `value_stock_record` | `value_stock_record → value_record` |

### Simple — 16 projects

| Project | Final symbol | Public helper graph |
| --- | --- | --- |
| `alphabetical-file-groups` | `group_filenames` | `group_filenames → classify_filename` |
| `billing-system` | `calculate_bill` | `calculate_bill → validate_bill_lines` |
| `calculate-age` | `summarize_age` | `summarize_age → calculate_age_days` |
| `calculator` | `calculate` | `calculate → validate_calculation` |
| `compute-iou` | `compute_iou` | `compute_iou → calculate_intersection_union` |
| `currency-converter` | `convert_currency` | `convert_currency → validate_conversion_request` |
| `decimal-binary` | `convert_binary_decimal` | `convert_binary_decimal → decimal_to_binary \| binary_to_decimal` |
| `json-to-csv` | `serialize_csv` | `serialize_csv → escape_csv_field` |
| `numbers-to-words` | `spell_cardinal` | `spell_cardinal → spell_under_thousand` |
| `random-password-generator` | `generate_password` | `generate_password → required_password_draws` |
| `rock-paper-scissors` | `decide_round` | `decide_round → user_beats_computer` |
| `split-file` | `split_lines` | `split_lines → validate_split_request` |
| `textfile-analysis` | `analyze_text` | `analyze_text → extract_casefolded_words` |
| `tic-tac-toe` | `apply_tic_tac_toe_move` | `apply_tic_tac_toe_move → validate_board_state` |
| `unique-words` | `find_unique_words` | `find_unique_words → normalize_words` |
| `website-connectivity` | `classify_websites` | `classify_websites → classify_observation` |

### Complex — 16 projects

| Project | Final symbol | Public helper graph |
| --- | --- | --- |
| `archive-request` | `plan_archive` | `plan_archive → canonicalize_archive_url, compose_archive_plan` |
| `artifact-pipeline` | `plan_pipeline` | `plan_pipeline → topologically_order_steps` |
| `backup-plan` | `plan_backup` | `plan_backup → validate_backup_request, classify_backup_paths` |
| `case-ranking` | `rank_cases` | `rank_cases → order_matching_cases → score_case_overlap` |
| `clip-ranges` | `plan_clip_ranges` | `plan_clip_ranges → range_duration_ms` |
| `color-quantization` | `quantize_colors` | `quantize_colors → rank_palette_colors` |
| `expense-split` | `settle_expense` | `settle_expense → calculate_balances, settle_balances` |
| `experiment-ranking` | `rank_experiments` | `rank_experiments → order_run_ids` |
| `flashcard-schedule` | `schedule_review` | `schedule_review → validate_review_ease` |
| `inventory-reorder` | `plan_reorder` | `plan_reorder → available_stock` |
| `move-2048` | `apply_2048_move` | `apply_2048_move → validate_2048_board, merge_move_line` |
| `page-build` | `build_page` | `build_page → render_page_html → escape_page_text` |
| `publication-workflow` | `transition_publication` | `transition_publication → transition_target` |
| `reputation` | `calculate_reputation` | `calculate_reputation → reputation_delta` |
| `roast-analysis` | `analyze_roast_profile` | `analyze_roast_profile → validate_roast_profile, summarize_roast_samples` |
| `track-metadata` | `normalize_track_metadata` | `normalize_track_metadata → trim_track_draft, format_track_metadata` |

## `process-bar`: focused full-generation fixture

`examples/complex/process-bar` is excluded from the 9/16/16 curriculum counts. It is the focused
integration fixture for generating an entire composed module:

```text
process_bar → validate_payload, process_payload_bytes, build_output
```

The fixture has no implementation mapping or `cott_bindings` source. Its four accepted generated
implementations are retained below `python/_cott_impl/foo/bar/` alongside the contract and
compiler-owned output tree.

```bash
project=examples/complex/process-bar
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # refreshes output; all four implementations stay resolved
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
```

Full generation invokes one function-scoped agent process for each eligible unresolved symbol and
retains the four accepted implementations below `python/_cott_impl/foo/bar/`. `process_bar`
orchestrates the three helpers through the generated `foo.bar` facade; the network effect declared
by `process_payload_bytes` remains declared by its caller. This fixture exercises the complete
unresolved-to-generated transition rather than teaching manifest binding.

## Editor analysis

Run the parameterless language server from a Cott project:

```bash
cott lsp
```

It serves editor diagnostics, completion, hover, and definition over stdio JSON-RPC using UTF-16
positions and full document sync. It analyzes open documents without generating, publishing, or
invoking an agent.
