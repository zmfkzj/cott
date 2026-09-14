# Authoring Cott modules and declarations

Read this reference before creating or changing a `.cott` contract. For function clauses and effects, continue with [contracts-and-effects.md](contracts-and-effects.md). Use [traits-and-scenarios.md](traits-and-scenarios.md) only for stateful protocols or finite scenarios.

## Start from the nearest example

Prefer an existing declaration shape over inventing a second style:

| Need | Maintained examples |
| --- | --- |
| Small function and enum | `examples/simple/calculator/src/curriculum/calculator.cott`; `examples/kotlin/simple/calculator/src/curriculum/calculator.cott` |
| Structs, imports, and payload errors | `examples/modular/order-management/src/store/`; `examples/kotlin/modular/order-management/src/store/` |
| Aliases, newtypes, constants, and generics | `examples/features/declarations-generics/src/declarations/`; `examples/kotlin/features/declarations-generics/src/declarations/` |
| JSON and recursive payload enums | `examples/features/json-transform/src/curriculum/json_transform.cott`; `examples/kotlin/features/json-transform/src/curriculum/json_transform.cott` |
| External, opaque, and iterator boundary types | `examples/features/boundary-protocols/src/curriculum/boundary_protocols.cott`; `examples/kotlin/features/boundary-protocols/src/curriculum/boundary_protocols.cott` |
| Dart package and Flutter boundary | `examples/integrations/flutter-counter/src/example/counter.cott` |

Copy the smallest relevant Cott pattern, then rename it for the domain. For target configuration and consumer boundaries, read [targets and deployment](targets-and-deployment.md).

## Match the module to the source path

A project source has one module per file. The path below `src/` determines the module name injectively:

```text
src/store/catalog.cott  ->  module store.catalog
src/store/order.cott    ->  module store.order
```

Import public symbols explicitly:

```cott
module store.order

use store.catalog.{Catalog, CatalogError}
```

Use four spaces. Tabs and semicolons are invalid.

## Model the domain before functions

Use built-in scalar and container types directly when they already express the boundary:

```cott
struct OrderLine:
    sku: Str
    quantity: U32

struct Order:
    order_id: Str
    lines: List[OrderLine]

enum OrderError:
    EmptyOrder
    InvalidQuantity(sku: Str)
    ItemUnavailable(cause: CatalogError)
```

Common shapes demonstrated by the maintained examples include:

- Scalars: `Bool`, signed and unsigned fixed-width integers such as `I32`, `I64`, `U32`, and `U64`, `F64`, `Str`, `Path`, `Unit`, and `Never`.
- Values and containers: `Option[T]`, `Result[T, E]`, `List[T]`, `Set[T]`, `Tuple[...]`, fixed `Array[T, N]`, `Buffer[N]`, and `JsonValue`.
- Boundaries and protocols: `Any`, `Unknown`, `Opaque["identity"]`, `Iterator[T]`, `Generator[Y, S, R]`, `AsyncIterator[T]`, and `AsyncGenerator[Y, S]`.

This is a practical example index, not a substitute for diagnostics. Let `cott check` reject an unsupported type or placement.

## Choose the lightest declaration

An alias renames a type without a new nominal boundary:

```cott
alias Label = Str
```

A newtype creates a nominal value and can refine construction:

```cott
newtype NonEmptyLabel(Label)
    where self.len > 0
```

A struct is immutable public data. Put invariants on relations that every constructed value must preserve:

```cott
struct LabelAssessment:
    text: Str
    length: U64
    label: NonEmptyLabel

    invariant self.text.len == self.length
    invariant self.text == self.label.value
```

Enum variants may be empty or carry typed payloads:

```cott
enum LookupError:
    Missing
    InvalidKey(key: Str)
```

Constants are typed:

```cott
const LABEL_BYTES: U64 = 4
```

Do not duplicate a `where`, `invariant`, or constant check in target implementation code. Generated constructors and facades own those boundaries.

## Add generics only when the public contract needs them

Type and const parameters are part of the public identity:

```cott
struct LabelFrame[+T]:
    label: NonEmptyLabel
    value: T

struct ByteBlock[const N: U64]:
    raw: Buffer[N]
```

Use concrete instantiations at call boundaries:

```cott
fn package_label(
    label: NonEmptyLabel,
    values: Array[U8, 4],
    raw: Buffer[4],
) -> Tuple[Label, LabelFrame[Array[U8, 4]], ByteBlock[4]]:
    requires values.len == LABEL_BYTES
    effects []
```

Do not introduce variance, const generics, `Any`, or `Unknown` for speculative flexibility. Use them only when the contract itself requires that boundary.

## Declare target-owned types explicitly

Use an external type when the public signature intentionally projects a target type:

```cott
external type HttpRequest

@get("/")
fn read_root(request: HttpRequest) -> HelloResponse:
    ensures result.message == "Hello World"
    effects []
```

The corresponding target mapping belongs in `cott.toml`; the `.cott` declaration remains the public semantic name. Python uses `module:Qualname`, Kotlin uses a Kotlin FQN, and Dart uses a library URI plus type name. See [targets and deployment](targets-and-deployment.md). Use `Opaque["identity"]` when callers may carry an identity but must not inspect its representation.

## Authoring sequence

1. Pick the source path and write its exact `module` declaration.
2. Add explicit `use` imports.
3. Define aliases, constants, newtypes, structs, and enums in dependency order.
4. Add bodyless public functions last.
5. Run `cott check --project <root> --format json` and fix the first source diagnostic.
6. Run `cott fmt --project <root> --format json`; never hand-align syntax against the formatter.
