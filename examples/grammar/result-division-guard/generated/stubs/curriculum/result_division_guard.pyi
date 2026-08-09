from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.result_division_guard_types import DivideError, ZeroDivisor
DivideError: TypeAlias = Union[ZeroDivisor]

def run() -> Result[int, DivideError]: ...
