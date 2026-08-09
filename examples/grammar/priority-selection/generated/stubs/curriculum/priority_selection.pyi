from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.priority_selection_types import Priority, High, Normal
Priority: TypeAlias = Union[High, Normal]

def run() -> Priority: ...
