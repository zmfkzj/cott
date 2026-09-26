from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.forge_types import ForgeError, ForgeError_Unresolved
from frogmouth.model_types import Forge, ForgeRequest, Location, LocationKind, LocationKind_Remote

def parse_forge_request(arguments: str) -> Option[ForgeRequest]:
    """Parse the arguments of a forge quick-view command. Leading and trailing
whitespace is removed as Python str.strip() does, then two Python regular
expressions are tried in order and the first that matches decides:

^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+)(?: +(?P<file>[^ ]+))?$
^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+):(?P<branch>[^ ]+)(?: +(?P<file>[^ ]+))?$

owner and repository are the owner and repo groups; branch and file are
the groups of those names, Nothing when they did not participate (the
first expression has no branch). Text neither expression matches is
Nothing."""
    arguments = _cott_validate_abi(arguments, str, path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/forge/parse_forge_request.py", "3eff4a562a75e4f24751c1990bfdec6f9bb52e10997ba8cdfd5ba6c0d0428859", "parse_forge_request", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.forge.parse_forge_request")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.forge.parse_forge_request"
        if _error.span is None:
            _error.span = {"end_byte":1233,"end_column":1,"end_line":30,"start_byte":138,"start_column":1,"start_line":8}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.forge.parse_forge_request", phase="implementation-call", span={"end_byte":1233,"end_column":1,"end_line":30,"start_byte":138,"start_column":1,"start_line":8}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.forge.parse_forge_request", phase="implementation-call", span={"end_byte":1233,"end_column":1,"end_line":30,"start_byte":138,"start_column":1,"start_line":8}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[ForgeRequest], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((request).owner in arguments)), "frogmouth.forge.parse_forge_request", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.forge.parse_forge_request", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.parse_forge_request", clause="ensures:1", phase="ensures", span={"end_byte":913,"end_column":71,"end_line":23,"start_byte":847,"start_column":5,"start_line":23}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((request).repository in arguments)), "frogmouth.forge.parse_forge_request", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.forge.parse_forge_request", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.parse_forge_request", clause="ensures:2", phase="ensures", span={"end_byte":989,"end_column":76,"end_line":24,"start_byte":918,"start_column":5,"start_line":24}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((not ("/" in (request).owner)) and (not (" " in (request).owner)))), "frogmouth.forge.parse_forge_request", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.forge.parse_forge_request", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.parse_forge_request", clause="ensures:3", phase="ensures", span={"end_byte":1097,"end_column":108,"end_line":25,"start_byte":994,"start_column":5,"start_line":25}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            request = _cott_match_value.value
            return (_cott_contract_condition((((not (":" in (request).repository)) and (not (" " in (request).repository)))), "frogmouth.forge.parse_forge_request", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.forge.parse_forge_request", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.parse_forge_request", clause="ensures:4", phase="ensures", span={"end_byte":1215,"end_column":118,"end_line":26,"start_byte":1102,"start_column":5,"start_line":26}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[ForgeRequest], path="$.return", validator=_cott_validate_abi)
    return _result

def forge_candidate_urls(forge: Forge, request: ForgeRequest) -> CottList[str]:
    """The raw-file URLs to probe, one per branch in probing order: request's
branch alone when it has one, otherwise "main" then "master". FILE is
request.file, or "README.md" when it has none. OWNER, REPOSITORY, BRANCH
and FILE are substituted verbatim into the forge's pattern:

GitHub:    https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/FILE
GitLab:    https://gitlab.com/OWNER/REPOSITORY/-/raw/BRANCH/FILE
BitBucket: https://bitbucket.org/OWNER/REPOSITORY/raw/BRANCH/FILE
Codeberg:  https://codeberg.org/OWNER/REPOSITORY/raw//branch/BRANCH/FILE"""
    forge = _cott_validate_abi(forge, Forge, path="$.forge")
    request = _cott_validate_abi(request, ForgeRequest, path="$.request")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/forge/forge_candidate_urls.py", "2fe9ba61ec30b6b506914e243e4a192caff74a901c7709de0266c66fe32b1729", "forge_candidate_urls", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.forge.forge_candidate_urls")
        _result = _implementation(forge, request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.forge.forge_candidate_urls"
        if _error.span is None:
            _error.span = {"end_byte":2073,"end_column":1,"end_line":48,"start_byte":1233,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.forge.forge_candidate_urls", phase="implementation-call", span={"end_byte":2073,"end_column":1,"end_line":48,"start_byte":1233,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.forge.forge_candidate_urls", phase="implementation-call", span={"end_byte":2073,"end_column":1,"end_line":48,"start_byte":1233,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = (request).branch
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition(((len(_result) == 1)), "frogmouth.forge.forge_candidate_urls", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.forge.forge_candidate_urls", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.forge_candidate_urls", clause="ensures:1", phase="ensures", span={"end_byte":1986,"end_column":69,"end_line":43,"start_byte":1922,"start_column":5,"start_line":43}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = (request).branch
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition(((len(_result) == 2)), "frogmouth.forge.forge_candidate_urls", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.forge.forge_candidate_urls", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.forge_candidate_urls", clause="ensures:2", phase="ensures", span={"end_byte":2055,"end_column":69,"end_line":44,"start_byte":1991,"start_column":5,"start_line":44}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def locate_forge_file(forge: Forge, candidates: CottList[str]) -> Result[Location, ForgeError]:
    """Find the first candidate URL that exists. Every candidate is an http or
https URL. Candidates are probed in order with an HTTP HEAD request
carrying the header "User-Agent: frogmouth v0.9.1", following redirects,
with a 5 second timeout for connecting and for each read; a server that
answers the HEAD request with status 405 or 501 is asked once more for
the same candidate with GET. The first candidate whose final status is
200-299 is returned as a Remote location whose target is that candidate
(not the redirect target). Any other final status moves on to the next
candidate. A transport failure (name resolution, connection, timeout or
a malformed response) ends probing at once. When probing ends without a
found candidate the result is Unresolved(forge)."""
    forge = _cott_validate_abi(forge, Forge, path="$.forge")
    candidates = _cott_validate_abi(candidates, CottList[str], path="$.candidates")
    if not (_cott_contract_condition(((len(candidates) > 0)), "frogmouth.forge.locate_forge_file", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.forge.locate_forge_file", clause="requires:1", phase="requires", span={"end_byte":3023,"end_column":32,"end_line":63,"start_byte":2996,"start_column":5,"start_line":63}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/forge/locate_forge_file.py", "f96756fe3f021d22cad779774888a41ca107e52b3247f594223f38d20cd28324", "locate_forge_file", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.forge.locate_forge_file")
        _result = _implementation(forge, candidates)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.forge.locate_forge_file"
        if _error.span is None:
            _error.span = {"end_byte":3227,"end_column":1,"end_line":72,"start_byte":2073,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.forge.locate_forge_file", phase="implementation-call", span={"end_byte":3227,"end_column":1,"end_line":72,"start_byte":2073,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.forge.locate_forge_file", phase="implementation-call", span={"end_byte":3227,"end_column":1,"end_line":72,"start_byte":2073,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Location, ForgeError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.forge.locate_forge_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ForgeError_Unresolved,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.forge.locate_forge_file", phase="error", span={"end_byte":3227,"end_column":1,"end_line":72,"start_byte":2073,"start_column":1,"start_line":48}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.forge.locate_forge_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.forge.locate_forge_file", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ForgeError_Unresolved:
        _cott_contract_condition(True, "frogmouth.forge.locate_forge_file", "error:4")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            location = _cott_match_value.value
            return (_cott_contract_condition((((location).kind == LocationKind_Remote())), "frogmouth.forge.locate_forge_file", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.forge.locate_forge_file", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.locate_forge_file", clause="ensures:2", phase="ensures", span={"end_byte":3096,"end_column":72,"end_line":65,"start_byte":3029,"start_column":5,"start_line":65}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is ForgeError_Unresolved and True:
            failed = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((failed == forge)), "frogmouth.forge.locate_forge_file", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.forge.locate_forge_file", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.forge.locate_forge_file", clause="ensures:3", phase="ensures", span={"end_byte":3169,"end_column":73,"end_line":66,"start_byte":3101,"start_column":5,"start_line":66}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Location, ForgeError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ForgeError", "ForgeError_Unresolved", "forge_candidate_urls", "locate_forge_file", "parse_forge_request"]
