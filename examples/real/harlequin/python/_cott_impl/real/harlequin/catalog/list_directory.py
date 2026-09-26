import os
from pathlib import Path

from cott_runtime import U64, CottList, Err, Ok, Option, Result
from real.harlequin.catalog_types import CatalogEntry, CatalogKind_Directory, CatalogKind_File, FileTreeError, FileTreeError_NotADirectory, FileTreeError_Unreadable


def _is_dir(entry: os.DirEntry[str]) -> bool:
    try:
        return entry.is_dir()
    except OSError:
        return False


def _sort_key(item: tuple[bool, str, Path]) -> tuple[int, str, str]:
    return (0 if item[0] else 1, item[1].casefold(), item[1])


def list_directory(path: Path, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], FileTreeError]:
    if not path.is_dir():
        return Err(error=FileTreeError_NotADirectory(path=path))
    base = path.absolute()
    items: list[tuple[bool, str, Path]] = []
    try:
        with os.scandir(path) as iterator:
            for entry in iterator:
                items.append((_is_dir(entry), entry.name, base / entry.name))
    except OSError as exc:
        return Err(error=FileTreeError_Unreadable(path=path, message=str(exc)))
    items.sort(key=lambda item: _sort_key(item))
    entries: list[CatalogEntry] = []
    for is_dir, name, full in items:
        text = str(full)
        entries.append(
            CatalogEntry(
                id=text,
                parent=parent,
                depth=depth,
                label=name,
                type_label="dir" if is_dir else "",
                kind=CatalogKind_Directory() if is_dir else CatalogKind_File(),
                qualified_identifier=text,
                query_name="'" + text.replace("'", "''") + "'",
                expandable=is_dir,
                loaded=False,
            )
        )
    return Ok(value=CottList(values=entries))
