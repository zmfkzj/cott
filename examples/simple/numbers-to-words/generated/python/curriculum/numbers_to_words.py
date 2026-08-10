from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

def spell_under_thousand(value: I64) -> str:
    """Spell one integer from zero through nine hundred ninety-nine.

Hundreds use `and` before a nonzero remainder. Words are lowercase and
separated by one ASCII space, without commas or hyphens."""
    value = _cott_validate_abi(value, I64, path="$.value")
    if not ((value >= 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.numbers_to_words.spell_under_thousand", clause="requires:1", phase="requires", span={"end_byte":331,"end_column":24,"end_line":11,"start_byte":312,"start_column":5,"start_line":11}, expected="true", actual="false")
    if not ((value < 1000)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.numbers_to_words.spell_under_thousand", clause="requires:2", phase="requires", span={"end_byte":357,"end_column":26,"end_line":12,"start_byte":336,"start_column":5,"start_line":12}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/numbers_to_words/spell_under_thousand.py", "7ec87a433f335f083a86806f6aaa1be2da8c154ff09e6dfb94e5b2ed16675162", "spell_under_thousand", expected_project_name="numbers-to-words", expected_cott_symbol="curriculum.numbers_to_words.spell_under_thousand")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.numbers_to_words.spell_under_thousand"
        if _error.span is None:
            _error.span = {"end_byte":388,"end_column":1,"end_line":16,"start_byte":36,"start_column":1,"start_line":3}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.numbers_to_words.spell_under_thousand", phase="implementation-call", span={"end_byte":388,"end_column":1,"end_line":16,"start_byte":36,"start_column":1,"start_line":3}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.numbers_to_words.spell_under_thousand", phase="implementation-call", span={"end_byte":388,"end_column":1,"end_line":16,"start_byte":36,"start_column":1,"start_line":3}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 3)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.numbers_to_words.spell_under_thousand", clause="ensures:3", phase="ensures", span={"end_byte":386,"end_column":28,"end_line":14,"start_byte":363,"start_column":5,"start_line":14}, expected="true", actual="false")
    return _result

def spell_cardinal(value: I64) -> str:
    """Render an I64 as a canonical English cardinal.

Zero is `Zero`. Negative values begin with `(negative) `. The first number
word is capitalized and all later words are lowercase. Words use one ASCII
space with no commas or hyphens.

The magnitude is visited in descending three-digit groups. Zero groups are
omitted; each nonzero group is spelled by spell_under_thousand and paired
with `thousand`, `million`, `billion`, `trillion`, `quadrillion`, or
`quintillion`, the greatest scale needed by I64. A final group below one
hundred follows a higher group with `and`. All I64 values, including the
minimum, are accepted without signed-I64 negation."""
    value = _cott_validate_abi(value, I64, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/numbers_to_words/spell_cardinal.py", "7ab5380e3749d49c1dcafd74ad9bcd55f6fbb24ff7b614484c40d33414bba8af", "spell_cardinal", expected_project_name="numbers-to-words", expected_cott_symbol="curriculum.numbers_to_words.spell_cardinal")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.numbers_to_words.spell_cardinal"
        if _error.span is None:
            _error.span = {"end_byte":1170,"end_column":1,"end_line":33,"start_byte":388,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.numbers_to_words.spell_cardinal", phase="implementation-call", span={"end_byte":1170,"end_column":1,"end_line":33,"start_byte":388,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.numbers_to_words.spell_cardinal", phase="implementation-call", span={"end_byte":1170,"end_column":1,"end_line":33,"start_byte":388,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 3)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.numbers_to_words.spell_cardinal", clause="ensures:1", phase="ensures", span={"end_byte":1169,"end_column":28,"end_line":32,"start_byte":1146,"start_column":5,"start_line":32}, expected="true", actual="false")
    return _result

__all__ = ["spell_cardinal", "spell_under_thousand"]
