from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import FileReference, QueryResult

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Table:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Vertical:
    pass

RenderLayout: TypeAlias = Union[RenderLayout_Table, RenderLayout_Vertical]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Csv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Tsv:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Json:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Markdown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportFormat_Sql:
    pass

ExportFormat: TypeAlias = Union[ExportFormat_Csv, ExportFormat_Tsv, ExportFormat_Json, ExportFormat_Markdown, ExportFormat_Sql]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderOptions:
    __hash__ = None
    layout: RenderLayout
    terminal_width: U16
    maximum_cell_width: U16
    maximum_rows: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "layout", _cott_validate_abi(self.layout, RenderLayout, path="$.layout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_cell_width", _cott_validate_abi(self.maximum_cell_width, U16, path="$.maximum_cell_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_rows", _cott_validate_abi(self.maximum_rows, U32, path="$.maximum_rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    __hash__ = None
    name: str
    foreground: str
    background: str
    accent: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "foreground", _cott_validate_abi(self.foreground, str, path="$.foreground"))
        if not _cott_validated_construction():
            object.__setattr__(self, "background", _cott_validate_abi(self.background, str, path="$.background"))
        if not _cott_validated_construction():
            object.__setattr__(self, "accent", _cott_validate_abi(self.accent, str, path="$.accent"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyBinding:
    __hash__ = None
    key: str
    command: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "command", _cott_validate_abi(self.command, str, path="$.command"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Keymap:
    __hash__ = None
    name: str
    bindings: CottList[KeyBinding]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bindings", _cott_validate_abi(self.bindings, CottList[KeyBinding], path="$.bindings"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExportRequest:
    __hash__ = None
    result: QueryResult
    format: ExportFormat
    destination: FileReference

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, QueryResult, path="$.result"))
        if not _cott_validated_construction():
            object.__setattr__(self, "format", _cott_validate_abi(self.format, ExportFormat, path="$.format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, FileReference, path="$.destination"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_InvalidWidth:
    __hash__ = None
    width: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_UnsupportedCell:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_DestinationDenied:
    __hash__ = None
    destination: FileReference

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderError_ExportFailed:
    __hash__ = None
    destination: FileReference
    message: str

RenderError: TypeAlias = Union[RenderError_InvalidWidth, RenderError_UnsupportedCell, RenderError_DestinationDenied, RenderError_ExportFailed]

"""Match destination.location as FileLocation_Local/S3; serialize row.values; use boto3 Any."""
__all__ = ["ExportFormat", "ExportFormat_Csv", "ExportFormat_Json", "ExportFormat_Markdown", "ExportFormat_Sql", "ExportFormat_Tsv", "ExportRequest", "KeyBinding", "Keymap", "RenderError", "RenderError_DestinationDenied", "RenderError_ExportFailed", "RenderError_InvalidWidth", "RenderError_UnsupportedCell", "RenderLayout", "RenderLayout_Table", "RenderLayout_Vertical", "RenderOptions", "Theme"]
