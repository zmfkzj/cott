from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_MissingDatabase:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_InvalidPort:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionError_PromptDisabled:
    pass

ConnectionError: TypeAlias = Union[ConnectionError_MissingDatabase, ConnectionError_InvalidPort, ConnectionError_PromptDisabled]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionInputs:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentInputs:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSettings:
    __hash__ = None
    host: str
    port: str
    user: str
    password: str
    database: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "host", _cott_validate_abi(self.host, str, path="$.host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "port", _cott_validate_abi(self.port, str, path="$.port"))
        if not _cott_validated_construction():
            object.__setattr__(self, "user", _cott_validate_abi(self.user, str, path="$.user"))
        if not _cott_validated_construction():
            object.__setattr__(self, "password", _cott_validate_abi(self.password, str, path="$.password"))
        if not _cott_validated_construction():
            object.__setattr__(self, "database", _cott_validate_abi(self.database, str, path="$.database"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PromptAction_UsePassword:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PromptAction_PromptPassword:
    pass

PromptAction: TypeAlias = Union[PromptAction_UsePassword, PromptAction_PromptPassword]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ColumnCatalog:
    __hash__ = None
    name: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TableCatalog:
    __hash__ = None
    schema: str
    name: str
    columns: CottList[ColumnCatalog]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "schema", _cott_validate_abi(self.schema, str, path="$.schema"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[ColumnCatalog], path="$.columns"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionRequest:
    __hash__ = None
    source: str
    cursor: U64
    catalog: CottList[TableCatalog]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "catalog", _cott_validate_abi(self.catalog, CottList[TableCatalog], path="$.catalog"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionResult:
    __hash__ = None
    candidates: CottList[str]
    replace_start: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "candidates", _cott_validate_abi(self.candidates, CottList[str], path="$.candidates"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_start", _cott_validate_abi(self.replace_start, U64, path="$.replace_start"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Horizontal:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderLayout_Vertical:
    pass

RenderLayout: TypeAlias = Union[RenderLayout_Horizontal, RenderLayout_Vertical]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderRequest:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[CottList[str]]
    terminal_width: U16
    vertical: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[CottList[str]], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "terminal_width", _cott_validate_abi(self.terminal_width, U16, path="$.terminal_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "vertical", _cott_validate_abi(self.vertical, bool, path="$.vertical"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RenderedQuery:
    __hash__ = None
    text: str
    layout: RenderLayout
    width: U16

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "layout", _cott_validate_abi(self.layout, RenderLayout, path="$.layout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "width", _cott_validate_abi(self.width, U16, path="$.width"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Tables:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Describe:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BackslashCommand_Unknown:
    pass

BackslashCommand: TypeAlias = Union[BackslashCommand_Quit, BackslashCommand_Help, BackslashCommand_Tables, BackslashCommand_Describe, BackslashCommand_Unknown]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QueryResult:
    __hash__ = None
    columns: CottList[str]
    rows: CottList[CottList[str]]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, CottList[CottList[str]], path="$.rows"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseError_ConnectionFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DatabaseError_QueryFailed:
    __hash__ = None
    message: str

DatabaseError: TypeAlias = Union[DatabaseError_ConnectionFailed, DatabaseError_QueryFailed]

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "ColumnCatalog", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_PromptDisabled", "ConnectionInputs", "ConnectionSettings", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EnvironmentInputs", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryResult", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "TableCatalog"]
