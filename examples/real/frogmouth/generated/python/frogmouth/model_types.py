from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Local:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LocationKind_Remote:
    pass

LocationKind: TypeAlias = Union[LocationKind_Local, LocationKind_Remote]

"""A place the viewer can show. A Local target is POSIX path text for the host
file system; a Remote target is an absolute http or https URL whose scheme is
lower case."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Location:
    __hash__ = None
    kind: LocationKind
    target: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, LocationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "target", _cott_validate_abi(self.target, str, path="$.target"))
        if not (_cott_contract_condition(((len((self).target) > 0)), "frogmouth.model.Location", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:0", phase="invariant", span={"end_byte":333,"end_column":34,"end_line":16,"start_byte":304,"start_column":5,"start_line":16}, expected="true", actual="false")
        if not (_cott_contract_condition((((not ((self).kind == LocationKind_Remote())) or (_cott_starts_with((self).target, "http://") or _cott_starts_with((self).target, "https://")))), "frogmouth.model.Location", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Location", clause="invariant:1", phase="invariant", span={"end_byte":463,"end_column":130,"end_line":17,"start_byte":338,"start_column":5,"start_line":17}, expected="true", actual="false")

"""Markdown text loaded from location, exactly as decoded, without a title or
other derived data."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    __hash__ = None
    location: Location
    markdown: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "location", _cott_validate_abi(self.location, Location, path="$.location"))
        if not _cott_validated_construction():
            object.__setattr__(self, "markdown", _cott_validate_abi(self.markdown, str, path="$.markdown"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PathKind_Missing:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PathKind_File:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PathKind_Directory:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PathKind_Other:
    pass

PathKind: TypeAlias = Union[PathKind_Missing, PathKind_File, PathKind_Directory, PathKind_Other]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Forge_GitHub:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Forge_GitLab:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Forge_BitBucket:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Forge_Codeberg:
    pass

Forge: TypeAlias = Union[Forge_GitHub, Forge_GitLab, Forge_BitBucket, Forge_Codeberg]

"""A repository file request of the forge quick view. A missing branch means
"try main, then master"; a missing file means README.md."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ForgeRequest:
    __hash__ = None
    owner: str
    repository: str
    branch: Option[str]
    file: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "owner", _cott_validate_abi(self.owner, str, path="$.owner"))
        if not _cott_validated_construction():
            object.__setattr__(self, "repository", _cott_validate_abi(self.repository, str, path="$.repository"))
        if not _cott_validated_construction():
            object.__setattr__(self, "branch", _cott_validate_abi(self.branch, Option[str], path="$.branch"))
        if not _cott_validated_construction():
            object.__setattr__(self, "file", _cott_validate_abi(self.file, Option[str], path="$.file"))
        if not (_cott_contract_condition(((len((self).owner) > 0)), "frogmouth.model.ForgeRequest", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.ForgeRequest", clause="invariant:0", phase="invariant", span={"end_byte":1032,"end_column":33,"end_line":49,"start_byte":1004,"start_column":5,"start_line":49}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((self).repository) > 0)), "frogmouth.model.ForgeRequest", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.ForgeRequest", clause="invariant:1", phase="invariant", span={"end_byte":1070,"end_column":38,"end_line":50,"start_byte":1037,"start_column":5,"start_line":50}, expected="true", actual="false")

"""Text for a modal dialog. Both fields are Rich console markup."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Dialog:
    __hash__ = None
    title: str
    message: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))
        if not (_cott_contract_condition(((len((self).title) > 0)), "frogmouth.model.Dialog", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.Dialog", clause="invariant:0", phase="invariant", span={"end_byte":1226,"end_column":33,"end_line":59,"start_byte":1198,"start_column":5,"start_line":59}, expected="true", actual="false")

"""Process facts the browser resolves locations against: the user's home
directory, the process working directory, and the configured Markdown file
suffixes (for example ".md")."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserContext:
    __hash__ = None
    home: str
    working_directory: str
    markdown_extensions: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "home", _cott_validate_abi(self.home, str, path="$.home"))
        if not _cott_validated_construction():
            object.__setattr__(self, "working_directory", _cott_validate_abi(self.working_directory, str, path="$.working_directory"))
        if not _cott_validated_construction():
            object.__setattr__(self, "markdown_extensions", _cott_validate_abi(self.markdown_extensions, CottList[str], path="$.markdown_extensions"))
        if not (_cott_contract_condition(((len((self).home) > 0)), "frogmouth.model.BrowserContext", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.BrowserContext", clause="invariant:0", phase="invariant", span={"end_byte":1546,"end_column":32,"end_line":71,"start_byte":1519,"start_column":5,"start_line":71}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((self).working_directory) > 0)), "frogmouth.model.BrowserContext", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.model.BrowserContext", clause="invariant:1", phase="invariant", span={"end_byte":1591,"end_column":45,"end_line":72,"start_byte":1551,"start_column":5,"start_line":72}, expected="true", actual="false")

__all__ = ["BrowserContext", "Dialog", "Document", "Forge", "ForgeRequest", "Forge_BitBucket", "Forge_Codeberg", "Forge_GitHub", "Forge_GitLab", "Location", "LocationKind", "LocationKind_Local", "LocationKind_Remote", "PathKind", "PathKind_Directory", "PathKind_File", "PathKind_Missing", "PathKind_Other"]
