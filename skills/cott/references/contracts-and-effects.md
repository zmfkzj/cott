# Authoring functions, contracts, and effects

Read [authoring-basics.md](authoring-basics.md) first. This reference covers public behavior clauses, not target implementation details.

## Keep public functions bodyless

A `.cott` function declares behavior; it does not contain an implementation body:

```cott
fn find_item(catalog: Catalog, sku: Str) -> Result[Item, CatalogError]:
    doc """
    Look up an item in the catalog by its SKU.
    """

    requires sku.len > 0

    ensures Result.Ok(item) => item.sku == sku

    error CatalogError.ItemNotFound

    effects []
```

Use `async fn` only when the public callable is asynchronous. Keep clause groups in this readable order: `doc`, `requires`, `ensures`, `error`, then `effects`. Preserve source order within repeated clauses because diagnostics and contract evidence identify them separately.

## Put input obligations in `requires`

A precondition states what callers must supply:

```cott
requires request_id > 0
requires values.len == LABEL_BYTES
```

Do not use a precondition for a domain failure that callers must observe as data. Return `Result` and declare the error instead.

## Relate outputs with `ensures`

Use `result` for a plain return value:

```cott
ensures result < limit
```

Pattern-match a `Result` branch when the postcondition applies only to that branch:

```cott
ensures Result.Ok(receipt) => receipt.order_id == order.order_id
ensures Result.Err(LabelEvidenceError.TooShort(actual)) => actual.len < request.minimum_length
```

Keep separate guarantees as separate `ensures` clauses. Each clause receives its own stable evidence identity.

Prefer short observable relations over prose-only promises. Use `doc` for intent, ordering, and behavior that the expression language cannot state completely.

## Declare every public error

Use a conditional clause when the triggering condition is expressible:

```cott
error OrderError.EmptyOrder when order.lines.len == 0
error OrderError.InvalidQuantity when line.quantity == 0
```

Use a bare clause when the implementation may produce the declared error but the contract cannot completely describe its trigger:

```cott
error CatalogError.ItemNotFound
error ArtifactPipelineError.Cycle
```

Bind a payload source only when the error payload must be related to matched input:

```cott
error LabelEvidenceError.TooShort with request.label matches Option.Some(text) when (text.len < request.minimum_length)
```

Error declaration order is observable. Put validation failures in the order implementations must report them; do not sort them cosmetically.

## Close the effect set

Declare pure functions explicitly:

```cott
effects []
```

For effectful work, list the exact capabilities used by the public operation:

```cott
effects [file.read]
effects [file.read, file.write]
effects [network]
effects [database.read, database.write]
effects [clock]
effects [random]
effects [process.exit]
```

Do not declare extra effects for possible future implementations. Do not hide an effect behind a helper: a function that performs or reaches effectful work must retain the correct public contract boundary.

Effect scenarios run only against compiler-owned isolated fixtures. If isolation is unavailable, the observation is `unobserved`; never substitute host files, host network, wall clock, or an unsandboxed process.

## Use rules only for real clause composition

Rules can form and refine reusable error sets:

```cott
rule BaselineLabelRule:
    error LabelEvidenceError.Legacy
    error LabelEvidenceError.Missing

rule RefinedLabelRule(BaselineLabelRule):
    override error LabelEvidenceError.Missing when false
    delete error LabelEvidenceError.Legacy
```

Do not create a rule for one function. Direct clauses are smaller and easier to inspect. Use `override` and `delete` only when inheritance is the actual public contract.

## Complete function example

```cott
module store.order

use store.catalog.{Catalog, CatalogError}

struct Order:
    order_id: Str
    lines: List[OrderLine]

struct OrderReceipt:
    order_id: Str
    total_items: U32
    total_cents: U64

enum OrderError:
    EmptyOrder
    InvalidQuantity(sku: Str)
    ItemUnavailable(cause: CatalogError)

fn calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]:
    doc """
    Validate all order lines, look up item prices, and produce a receipt.
    """

    ensures Result.Ok(receipt) => receipt.order_id == order.order_id

    error OrderError.EmptyOrder when order.lines.len == 0
    error OrderError.InvalidQuantity
    error OrderError.ItemUnavailable

    effects []
```

## Contract review

Before generating an implementation, check:

- The return type exposes expected failures as `Result`, not exceptions hidden from the contract.
- Preconditions describe caller obligations, while errors describe observable domain failures.
- Success and error payloads are related to inputs where the expression language permits it.
- Error order matches required precedence.
- `effects` is exact and closed.
- The function remains bodyless.

Then run:

```bash
cott check --project "$project" --format json
cott fmt --check --project "$project" --format json
cott emit ir --project "$project" --format json
```

Inspect Canonical IR only to confirm the compiler's interpretation; never edit it as a second source of truth.
