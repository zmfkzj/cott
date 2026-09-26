from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.model_types import BrowserContext as BrowserContext, Dialog as Dialog, Document as Document, Forge as Forge, ForgeRequest as ForgeRequest, Forge_BitBucket as Forge_BitBucket, Forge_Codeberg as Forge_Codeberg, Forge_GitHub as Forge_GitHub, Forge_GitLab as Forge_GitLab, Location as Location, LocationKind as LocationKind, LocationKind_Local as LocationKind_Local, LocationKind_Remote as LocationKind_Remote, PathKind as PathKind, PathKind_Directory as PathKind_Directory, PathKind_File as PathKind_File, PathKind_Missing as PathKind_Missing, PathKind_Other as PathKind_Other
__all__ = ["BrowserContext", "Dialog", "Document", "Forge", "ForgeRequest", "Forge_BitBucket", "Forge_Codeberg", "Forge_GitHub", "Forge_GitLab", "Location", "LocationKind", "LocationKind_Local", "LocationKind_Remote", "PathKind", "PathKind_Directory", "PathKind_File", "PathKind_Missing", "PathKind_Other"]
