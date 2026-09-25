# declarations-generics

## Purpose
This runnable feature example packages a fixed-width label frame and its raw bytes through an agent-generated Python implementation.

## Key points
- `core.cott` defines the `Label` alias, the `LABEL_BYTES` `U64` constant, the refined `NonEmptyLabel` nominal type, and the `ByteBlock[const N: U64]` buffer wrapper; the app constructs the newtype before calling the facade.
- `LabelFrame[+T]` is a covariant declaration: its `value: T` field uses `T` only in positive position. `package_label` instantiates it with the fixed-size `Array[U8, LABEL_BYTES]` payload.
- `presentation.cott` imports those public symbols with `use` and uses the imported constant as the width of its public types: `Array[U8, LABEL_BYTES]`, `Buffer[LABEL_BYTES]` and `ByteBlock[LABEL_BYTES]`. The types fix the length, so no length precondition is needed. It returns a heterogeneous `Tuple` of the label's text, a covariant `LabelFrame[Array[U8, LABEL_BYTES]]` and `ByteBlock[LABEL_BYTES]` raw bytes.
- Contracts cannot index tuples, so the output relation is requirement `RETURNS_INPUTS_UNCHANGED`: the tuple carries the label's text, `LabelFrame(label, values)` and `ByteBlock(raw)` unchanged. Scenario `package_label_keeps_inputs` compares the whole tuple for one input and is its linked check.
