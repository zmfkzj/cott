from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.posting.client_types import Header as Header, HttpMethod as HttpMethod, HttpMethod_Custom as HttpMethod_Custom, HttpMethod_Delete as HttpMethod_Delete, HttpMethod_Get as HttpMethod_Get, HttpMethod_Head as HttpMethod_Head, HttpMethod_Options as HttpMethod_Options, HttpMethod_Patch as HttpMethod_Patch, HttpMethod_Post as HttpMethod_Post, HttpMethod_Put as HttpMethod_Put, PostingError as PostingError, PostingError_InvalidArguments as PostingError_InvalidArguments, PostingError_InvalidRequest as PostingError_InvalidRequest, PostingError_NetworkFailed as PostingError_NetworkFailed, Request as Request, Response as Response
"""Accept standard HTTP methods case-insensitively; preserve other non-empty methods."""
def parse_method(source: str) -> Result[HttpMethod, PostingError]: ...

"""Parse METHOD URL [BODY]; use a 30-second timeout and no headers."""
def parse_arguments(arguments: CottList[str]) -> Result[Request, PostingError]: ...

"""Send one HTTP request and retain status, final URL, headers, and response bytes."""
def send_request(request: Request) -> Result[Response, PostingError]: ...

"""Render status and final URL, then headers and a UTF-8 replacement-decoded body."""
def render_response(response: Response) -> str: ...

"""Parse arguments, send the request, and render its response."""
def execute(arguments: CottList[str]) -> Result[str, PostingError]: ...

__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response", "execute", "parse_arguments", "parse_method", "render_response", "send_request"]
