# declarations-generics

## Purpose
This runnable v0.7 feature example packages a fixed-width label frame and its raw bytes through a manifest-bound Python implementation.

## Key points
- `core.cott` defines the `Label` alias, `LABEL_BYTES` `U64` constant, refined `NonEmptyLabel` nominal type, and `ByteBlock[const N: U64]` buffer wrapper; the app constructs the newtype before calling the facade.
- `LabelFrame[+T]` is a covariant declaration: its `value: T` field uses `T` only in positive position. `package_label` instantiates it with the fixed-size `Array[U8, 4]` payload.
- `presentation.cott` imports those public symbols with `use`, uses literal fixed-size `Array[U8, 4]` and `Buffer[4]` public types, and keeps `LABEL_BYTES` observable through `requires values.len == LABEL_BYTES`. It returns a heterogeneous `Tuple` containing the alias value, a covariant `LabelFrame[Array[U8, 4]]`, and `ByteBlock[4]` raw bytes.
