from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.contracts_evidence_types import AcceptedLabel as AcceptedLabel, BaselineLabelRule as BaselineLabelRule, LabelAssessment as LabelAssessment, LabelEvidenceError as LabelEvidenceError, LabelEvidenceError_Legacy as LabelEvidenceError_Legacy, LabelEvidenceError_Missing as LabelEvidenceError_Missing, LabelEvidenceError_TooShort as LabelEvidenceError_TooShort, LabelRequest as LabelRequest, RefinedLabelRule as RefinedLabelRule
"""Assess labels directly: missing labels and labels shorter than the requested
minimum are declared errors; successful labels are nominally refined and
meet the request's minimum length."""
def assess_label(request: LabelRequest) -> Result[LabelAssessment, LabelEvidenceError]: ...

__all__ = ["AcceptedLabel", "BaselineLabelRule", "LabelAssessment", "LabelEvidenceError", "LabelEvidenceError_Legacy", "LabelEvidenceError_Missing", "LabelEvidenceError_TooShort", "LabelRequest", "RefinedLabelRule", "assess_label"]
