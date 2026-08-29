from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli_types import BackslashCommand as BackslashCommand, BackslashCommand_Describe as BackslashCommand_Describe, BackslashCommand_Help as BackslashCommand_Help, BackslashCommand_Quit as BackslashCommand_Quit, BackslashCommand_Tables as BackslashCommand_Tables, BackslashCommand_Unknown as BackslashCommand_Unknown, ColumnCatalog as ColumnCatalog, CompletionRequest as CompletionRequest, CompletionResult as CompletionResult, ConnectionError as ConnectionError, ConnectionError_InvalidPort as ConnectionError_InvalidPort, ConnectionError_MissingDatabase as ConnectionError_MissingDatabase, ConnectionError_PromptDisabled as ConnectionError_PromptDisabled, ConnectionInputs as ConnectionInputs, ConnectionSettings as ConnectionSettings, DatabaseError as DatabaseError, DatabaseError_ConnectionFailed as DatabaseError_ConnectionFailed, DatabaseError_QueryFailed as DatabaseError_QueryFailed, EnvironmentInputs as EnvironmentInputs, PromptAction as PromptAction, PromptAction_PromptPassword as PromptAction_PromptPassword, PromptAction_UsePassword as PromptAction_UsePassword, QueryResult as QueryResult, RenderLayout as RenderLayout, RenderLayout_Horizontal as RenderLayout_Horizontal, RenderLayout_Vertical as RenderLayout_Vertical, RenderRequest as RenderRequest, RenderedQuery as RenderedQuery, TableCatalog as TableCatalog
def resolve_connection(inputs: ConnectionInputs, environment: EnvironmentInputs) -> Result[ConnectionSettings, ConnectionError]: ...

def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]: ...

def complete_sql(request: CompletionRequest) -> CompletionResult: ...

def render_query(request: RenderRequest) -> RenderedQuery: ...

def recognize_backslash(source: str) -> BackslashCommand: ...

def execute_query(connection: ConnectionSettings, sql: str) -> Result[QueryResult, DatabaseError]: ...

__all__ = ["BackslashCommand", "BackslashCommand_Describe", "BackslashCommand_Help", "BackslashCommand_Quit", "BackslashCommand_Tables", "BackslashCommand_Unknown", "ColumnCatalog", "CompletionRequest", "CompletionResult", "ConnectionError", "ConnectionError_InvalidPort", "ConnectionError_MissingDatabase", "ConnectionError_PromptDisabled", "ConnectionInputs", "ConnectionSettings", "DatabaseError", "DatabaseError_ConnectionFailed", "DatabaseError_QueryFailed", "EnvironmentInputs", "PromptAction", "PromptAction_PromptPassword", "PromptAction_UsePassword", "QueryResult", "RenderLayout", "RenderLayout_Horizontal", "RenderLayout_Vertical", "RenderRequest", "RenderedQuery", "TableCatalog", "complete_sql", "execute_query", "prompt_policy", "recognize_backslash", "render_query", "resolve_connection"]
