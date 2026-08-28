from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.publication_workflow_types import PublicationAction, PublicationAction_Approve, PublicationAction_Submit, PublicationAction_Withdraw, PublicationRequest, PublicationState, PublicationState_Draft, PublicationState_InReview, PublicationState_Published, PublicationState_Withdrawn, PublicationWorkflowError, PublicationWorkflowError_ApprovalRequired, PublicationWorkflowError_InvalidTransition

def transition_target(current: PublicationState, action: PublicationAction) -> Option[PublicationState]:
    """Return the publication state selected by the workflow transition table, or
Nothing when the state and action do not form a valid transition."""
    current = _cott_validate_abi(current, PublicationState, path="$.current")
    action = _cott_validate_abi(action, PublicationAction, path="$.action")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/publication_workflow/transition_target.py", "80330a4d4ba5f101c6e3eb539d0d3381da102a27d7abca992396cba380f8a37c", "transition_target", expected_project_name="publication-workflow", expected_cott_symbol="curriculum.publication_workflow.transition_target")
        _result = _implementation(current, action)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.publication_workflow.transition_target"
        if _error.span is None:
            _error.span = {"end_byte":720,"end_column":1,"end_line":36,"start_byte":369,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.publication_workflow.transition_target", phase="implementation-call", span={"end_byte":720,"end_column":1,"end_line":36,"start_byte":369,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.publication_workflow.transition_target", phase="implementation-call", span={"end_byte":720,"end_column":1,"end_line":36,"start_byte":369,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[PublicationState], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            next = _cott_match_value.value
            return ((next != current))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.publication_workflow.transition_target", clause="ensures:1", phase="ensures", span={"end_byte":702,"end_column":49,"end_line":32,"start_byte":658,"start_column":5,"start_line":32}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[PublicationState], path="$.return", validator=_cott_validate_abi)
    return _result

def transition_publication(request: PublicationRequest) -> Result[PublicationState, PublicationWorkflowError]:
    """Enforce approval and apply the publication workflow transition requested."""
    request = _cott_validate_abi(request, PublicationRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((((request).current == PublicationState_InReview()) and ((request).action == PublicationAction_Approve())) and (not (request).has_editor_approval))):
        _expected_error = PublicationWorkflowError_ApprovalRequired
        _expected_error_span = {"end_byte":1179,"end_column":188,"end_line":45,"start_byte":996,"start_column":5,"start_line":45}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/publication_workflow/transition_publication.py", "0963f8f82615dd9c6572c912d0557ae59321e766495f054a79f713bb29b224f4", "transition_publication", expected_project_name="publication-workflow", expected_cott_symbol="curriculum.publication_workflow.transition_publication")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.publication_workflow.transition_publication"
        if _error.span is None:
            _error.span = {"end_byte":1249,"end_column":1,"end_line":49,"start_byte":720,"start_column":1,"start_line":36}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.publication_workflow.transition_publication", phase="implementation-call", span={"end_byte":1249,"end_column":1,"end_line":49,"start_byte":720,"start_column":1,"start_line":36}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.publication_workflow.transition_publication", phase="implementation-call", span={"end_byte":1249,"end_column":1,"end_line":49,"start_byte":720,"start_column":1,"start_line":36}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PublicationState, PublicationWorkflowError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.publication_workflow.transition_publication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PublicationWorkflowError_InvalidTransition,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.publication_workflow.transition_publication", phase="error", span={"end_byte":1249,"end_column":1,"end_line":49,"start_byte":720,"start_column":1,"start_line":36}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.publication_workflow.transition_publication", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            next = _cott_match_value.value
            return ((next != (request).current))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.publication_workflow.transition_publication", clause="ensures:1", phase="ensures", span={"end_byte":990,"end_column":55,"end_line":43,"start_byte":940,"start_column":5,"start_line":43}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PublicationState, PublicationWorkflowError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["PublicationAction", "PublicationAction_Approve", "PublicationAction_Submit", "PublicationAction_Withdraw", "PublicationRequest", "PublicationState", "PublicationState_Draft", "PublicationState_InReview", "PublicationState_Published", "PublicationState_Withdrawn", "PublicationWorkflowError", "PublicationWorkflowError_ApprovalRequired", "PublicationWorkflowError_InvalidTransition", "transition_publication", "transition_target"]
