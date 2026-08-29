from __future__ import annotations

from typing import Literal

from cott_runtime import CottArray, CottBuffer, U8
from declarations.core_types import ByteBlock, LabelFrame, NonEmptyLabel


def package_label(label: NonEmptyLabel, values: CottArray[U8, Literal[4]], raw: CottBuffer[Literal[4]]) -> tuple[str, LabelFrame[CottArray[U8, Literal[4]]], ByteBlock[Literal[4]]]:
    return (label.value, LabelFrame(label=label, value=values), ByteBlock(raw=raw))
