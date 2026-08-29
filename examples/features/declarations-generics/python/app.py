from __future__ import annotations

from cott_runtime import CottArray, CottBuffer
from declarations.core_types import NonEmptyLabel
from declarations.presentation import package_label

label, frame, block = package_label(
    NonEmptyLabel(value="Cott"),
    CottArray(values=(3, 1, 4, 1)),
    CottBuffer(data=b"cott"),
)
print(f"label={label}; values={tuple(frame.value)}; bytes={block.raw.data.hex()}")
