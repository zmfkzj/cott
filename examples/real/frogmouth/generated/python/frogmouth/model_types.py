from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Location:
    __hash__ = None
    kind: LocationKind
    target: str
    fragment: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, LocationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "target", _cott_validate_abi(self.target, str, path="$.target"))
        if not _cott_validated_construction():
            object.__setattr__(self, "fragment", _cott_validate_abi(self.fragment, Option[str], path="$.fragment"))
        if not ((len((self).target) > 0)):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:0", phase="invariant", span={"end_byte":140,"end_column":34,"end_line":8,"start_byte":111,"start_column":5,"start_line":8}, expected="true", actual="false")
        if not ((((self).kind != LocationKind_Remote()) or (_cott_starts_with((self).target, "http://") or _cott_starts_with((self).target, "https://")))):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:1", phase="invariant", span={"end_byte":270,"end_column":130,"end_line":9,"start_byte":145,"start_column":5,"start_line":9}, expected="true", actual="false")
        if not ((((self).kind != LocationKind_Remote()) or (not ("#" in (self).target)))):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:2", phase="invariant", span={"end_byte":351,"end_column":81,"end_line":10,"start_byte":275,"start_column":5,"start_line":10}, expected="true", actual="false")
        if not ((((self).kind != LocationKind_GitHub()) or ("/" in (self).target))):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:3", phase="invariant", span={"end_byte":428,"end_column":77,"end_line":11,"start_byte":356,"start_column":5,"start_line":11}, expected="true", actual="false")
        if not ((((self).kind != LocationKind_Codeberg()) or ("/" in (self).target))):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:4", phase="invariant", span={"end_byte":507,"end_column":79,"end_line":12,"start_byte":433,"start_column":5,"start_line":12}, expected="true", actual="false")
        def _cott_match_invariant_5() -> bool:
            _cott_match_value = (self).fragment
            if type(_cott_match_value) is Some and True:
                fragment = _cott_match_value.value
                return (((len(fragment) > 0) and (not _cott_starts_with(fragment, "#"))))
            return True
        if not (_cott_match_invariant_5()):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:5", phase="invariant", span={"end_byte":622,"end_column":115,"end_line":13,"start_byte":512,"start_column":5,"start_line":13}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    __hash__ = None
    location: Location
    markdown: str
    title: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, Location, path="$.location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "markdown", _cott_validate_abi(self.markdown, str, path="$.markdown"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not ((len((self).title) > 0)):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Document", clause="invariant:0", phase="invariant", span={"end_byte":730,"end_column":33,"end_line":20,"start_byte":702,"start_column":5,"start_line":20}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserState:
    __hash__ = None
    history: CottList[str]
    bookmarks: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, CottList[str], path="$.history"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bookmarks", _cott_validate_abi(self.bookmarks, CottList[str], path="$.bookmarks"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Local:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Remote:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_GitHub:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Codeberg:
    pass

LocationKind: TypeAlias = Union[LocationKind_Local, LocationKind_Remote, LocationKind_GitHub, LocationKind_Codeberg]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StateAction_AddHistory:
    __hash__ = None
    location: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StateAction_ToggleBookmark:
    __hash__ = None
    location: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StateAction_RemoveHistory:
    __hash__ = None
    location: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StateAction_ClearHistory:
    pass

StateAction: TypeAlias = Union[StateAction_AddHistory, StateAction_ToggleBookmark, StateAction_RemoveHistory, StateAction_ClearHistory]

__all__ = ["BrowserState", "Document", "Location", "LocationKind", "LocationKind_Codeberg", "LocationKind_GitHub", "LocationKind_Local", "LocationKind_Remote", "StateAction", "StateAction_AddHistory", "StateAction_ClearHistory", "StateAction_RemoveHistory", "StateAction_ToggleBookmark"]
