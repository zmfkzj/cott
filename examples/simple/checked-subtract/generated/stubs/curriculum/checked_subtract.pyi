from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.checked_subtract_types import CountError, Underflow
CountError: TypeAlias = Union[Underflow]

def run() -> Result[int, CountError]: ...
