from typing import Any, Final, cast

import boto3
import botocore.exceptions

from cott_runtime import CottList, Err, Ok, Option, Result, Some, U64
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Bucket, CatalogKind_Object, CatalogKind_Prefix, S3Error, S3Error_AccessDenied, S3Error_Failed, S3Error_Unavailable

_ACCESS_CODES: Final[str] = "AccessDenied|AllAccessDisabled|AllBucketsAccessDenied|403"


def _entry(entry_id: str, parent: Option[str], depth: U64, label: str, type_label: str, kind: CatalogKind, expandable: bool) -> CatalogEntry:
    return CatalogEntry(
        id=entry_id,
        parent=parent,
        depth=depth,
        label=label,
        type_label=type_label,
        kind=kind,
        qualified_identifier=entry_id,
        query_name="'" + entry_id.replace("'", "''") + "'",
        expandable=expandable,
        loaded=False,
    )


def _bucket(name: str, parent: Option[str], depth: U64) -> CatalogEntry:
    return _entry("s3://" + name, parent, depth, name, "bkt", CatalogKind_Bucket(), True)


def _classify(target: str, exc: Exception) -> Result[CottList[CatalogEntry], S3Error]:
    exceptions: Any = botocore.exceptions
    unavailable: tuple[type[Exception], ...] = (
        cast(type[Exception], exceptions.NoCredentialsError),
        cast(type[Exception], exceptions.PartialCredentialsError),
        cast(type[Exception], exceptions.CredentialRetrievalError),
        cast(type[Exception], exceptions.NoRegionError),
    )
    if isinstance(exc, unavailable):
        error: S3Error = S3Error_Unavailable(message=str(exc))
        return Err(error=error)
    client_error = cast(type[Exception], exceptions.ClientError)
    if isinstance(exc, client_error):
        raw: Any = exc
        response = cast(object, raw.response)
        code = ""
        server_message = ""
        if isinstance(response, dict):
            err_part = cast(dict[str, object], response).get("Error")
            if isinstance(err_part, dict):
                err_dict = cast(dict[str, object], err_part)
                code_raw = err_dict.get("Code")
                if isinstance(code_raw, str):
                    code = code_raw
                message_raw = err_dict.get("Message")
                if isinstance(message_raw, str):
                    server_message = message_raw
        if code in _ACCESS_CODES.split("|"):
            denied: S3Error = S3Error_AccessDenied(target=target)
            return Err(error=denied)
        detail = "S3 returned error " + (code or "unknown")
        if server_message:
            detail += ": " + server_message
        rejected: S3Error = S3Error_Failed(target=target, message=detail)
        return Err(error=rejected)
    failed: S3Error = S3Error_Failed(target=target, message="S3 request failed (network, endpoint or configuration error)")
    return Err(error=failed)


def _list(target: str, parent: Option[str], depth: U64) -> CottList[CatalogEntry]:
    sdk: Any = boto3
    client: Any = sdk.client("s3")
    entries: list[CatalogEntry] = []
    if target == "all":
        response = cast(object, client.list_buckets())
        if isinstance(response, dict):
            buckets = cast(dict[str, object], response).get("Buckets")
            if isinstance(buckets, list):
                for item in cast(list[object], buckets):
                    if isinstance(item, dict):
                        name = cast(dict[str, object], item).get("Name")
                        if isinstance(name, str):
                            entries.append(_bucket(name, parent, depth))
        return CottList(values=entries)
    path = target[len("s3://"):] if target.startswith("s3://") else target
    bucket, _, prefix = path.partition("/")
    paginator: Any = client.get_paginator("list_objects_v2")
    prefixes: list[CatalogEntry] = []
    objects: list[CatalogEntry] = []
    pages: Any = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")
    for page_raw in pages:
        page = cast(object, page_raw)
        if not isinstance(page, dict):
            continue
        page_dict = cast(dict[str, object], page)
        common = page_dict.get("CommonPrefixes")
        if isinstance(common, list):
            for item in cast(list[object], common):
                if isinstance(item, dict):
                    value = cast(dict[str, object], item).get("Prefix")
                    if isinstance(value, str):
                        label = value.rstrip("/").rsplit("/", 1)[-1] + "/"
                        prefixes.append(_entry("s3://" + bucket + "/" + value, parent, depth, label, "dir", CatalogKind_Prefix(), True))
        contents = page_dict.get("Contents")
        if isinstance(contents, list):
            for item in cast(list[object], contents):
                if isinstance(item, dict):
                    key = cast(dict[str, object], item).get("Key")
                    if isinstance(key, str) and key != prefix:
                        objects.append(_entry("s3://" + bucket + "/" + key, parent, depth, key.rsplit("/", 1)[-1], "", CatalogKind_Object(), False))
    return CottList(values=prefixes + objects)


def list_s3(target: str, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], S3Error]:
    if not isinstance(parent, Some) and not target.startswith("s3://") and target != "all" and "/" not in target:
        return Ok(value=CottList(values=[_bucket(target, parent, depth)]))
    try:
        return Ok(value=_list(target, parent, depth))
    except Exception as exc:
        return _classify(target, exc)
