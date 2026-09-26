from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.hsql_types import CatalogPath, HsqlError, HsqlError_Usage


def _usage(message: str) -> Result[CatalogPath, HsqlError]:
    return Err(error=HsqlError_Usage(message=message))


def parse_catalog_path(path: str) -> Result[CatalogPath, HsqlError]:
    if path.strip() == "":
        return Ok(value=CatalogPath(segments=CottList(values=[]), pattern=Nothing()))
    segments: list[str] = []
    bare: list[bool] = []
    i = 0
    n = len(path)
    while True:
        if i < n and path[i] == '"':
            start = i
            j = i + 1
            chars: list[str] = []
            closed = False
            while j < n:
                if path[j] == '"':
                    if j + 1 < n and path[j + 1] == '"':
                        chars.append('"')
                        j += 2
                        continue
                    closed = True
                    j += 1
                    break
                chars.append(path[j])
                j += 1
            if not closed:
                return _usage(f"The quoted segment starting at {path[start:]} never closes. Write a literal quote as \"\".")
            if j < n and path[j] != ".":
                end = path.find(".", j)
                segment = path[start:] if end < 0 else path[start:end]
                return _usage(f"'{segment}' mixes quoted and bare text. Quote the whole segment or none of it.")
            segments.append("".join(chars))
            bare.append(False)
            i = j
        else:
            end = path.find(".", i)
            segment = path[i:] if end < 0 else path[i:end]
            if segment == "":
                return _usage(f"'{path}' has an empty segment. Separate labels with one dot, and quote a label that contains a dot, like \"my.table\".")
            if '"' in segment:
                return _usage(f"'{segment}' mixes quoted and bare text. Quote the whole segment or none of it.")
            segments.append(segment)
            bare.append(True)
            i = n if end < 0 else end
        if i >= n:
            break
        i += 1
        if i >= n:
            return _usage(f"'{path}' has an empty segment. Separate labels with one dot, and quote a label that contains a dot, like \"my.table\".")
    for k in range(len(segments) - 1):
        if bare[k] and ("*" in segments[k] or "?" in segments[k]):
            return _usage(f"'{segments[k]}' contains a wildcard in the middle of a path, which is not supported. A wildcard is only allowed in the last path segment.")
    last = segments[-1]
    if bare[-1] and ("*" in last or "?" in last):
        return Ok(value=CatalogPath(segments=CottList(values=segments[:-1]), pattern=Some(value=last)))
    return Ok(value=CatalogPath(segments=CottList(values=segments), pattern=Nothing()))
