from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.parity_classification_types import Parity, Even, Odd
Parity: TypeAlias = Union[Even, Odd]

def run() -> Parity: ...
