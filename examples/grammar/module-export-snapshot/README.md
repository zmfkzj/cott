# module-export-snapshot

## Purpose
Demonstrates a return-value contract that independently preserves same-name-family module inputs in structure fields.

## Key points
- `ModuleSnapshot` has separate `I64` fields named `exported_x` and `module_x`, and `build_snapshot` accepts the same two inputs.
- The two `ensures` declarations state that each returned field equals its corresponding input, prohibiting cross-assignment or value conversion.
- The Python implementation passes both arguments unchanged to `ModuleSnapshot(exported_x=..., module_x=...)`, preserving every `I64` boundary value and equal input values.
