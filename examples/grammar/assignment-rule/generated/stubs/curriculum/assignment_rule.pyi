from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.assignment_rule_types import Assignment as Assignment, BaseAssignmentRule as BaseAssignmentRule, ParseAssignmentError as ParseAssignmentError, ParseAssignmentError_EmptyName as ParseAssignmentError_EmptyName, ParseAssignmentError_MissingEquals as ParseAssignmentError_MissingEquals, StrictAssignmentRule as StrictAssignmentRule
"""Parses one assignment without I/O or mutation following strict rules."""
def parse_assignment(line: str) -> Result[Assignment, ParseAssignmentError]: ...

__all__ = ["Assignment", "BaseAssignmentRule", "ParseAssignmentError", "ParseAssignmentError_EmptyName", "ParseAssignmentError_MissingEquals", "StrictAssignmentRule", "parse_assignment"]
