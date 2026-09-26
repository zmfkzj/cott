from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Bucket, CatalogKind_Column, CatalogKind_Database, CatalogKind_Directory, CatalogKind_File, CatalogKind_Object, CatalogKind_Other, CatalogKind_Prefix, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View, Completion, CompletionSet, FileTreeError, FileTreeError_NotADirectory, FileTreeError_Unreadable, S3Error, S3Error_AccessDenied, S3Error_Failed, S3Error_Unavailable, TreeFrame, TreeMotion, TreeMotion_Down, TreeMotion_First, TreeMotion_Last, TreeMotion_PageDown, TreeMotion_PageUp, TreeMotion_Parent, TreeMotion_Up, TreeState, TreeToggle
from real.harlequin.style_types import StyledLine

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def normalize_catalog(entries: CottList[CatalogEntry]) -> CottList[CatalogEntry]:
    """Put catalog entries into catalog order. A catalog is a List[CatalogEntry] in
pre-order: every entry is followed by its whole subtree before its next
sibling, ids unique. Input entries may come in any order where every parent
appears before its children. Children keep their relative input order under
their parent and roots keep theirs. An entry whose parent id is not an
earlier kept entry, or whose id repeats an earlier kept entry, is dropped
together with its descendants. depth is recomputed from the parent chain
(roots 0), and every entry that has children is marked expandable and
loaded. Catalogs may hold tens of thousands of entries; the list is passed
as a whole, never embedded in another struct."""
    entries = _cott_normalize_f32_abi(entries, CottList[CatalogEntry], path="$.entries")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/normalize_catalog.py", "b6055a05951e084a6b7be5bbdee93c5296e5ed18caba803d3f6ceec5806c1dd4", "normalize_catalog", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.normalize_catalog")
        _result = _implementation(entries)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.normalize_catalog"
        if _error.span is None:
            _error.span = {"end_byte":3900,"end_column":1,"end_line":125,"start_byte":3001,"start_column":1,"start_line":107}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.normalize_catalog", phase="implementation-call", span={"end_byte":3900,"end_column":1,"end_line":125,"start_byte":3001,"start_column":1,"start_line":107}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.normalize_catalog", phase="implementation-call", span={"end_byte":3900,"end_column":1,"end_line":125,"start_byte":3001,"start_column":1,"start_line":107}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[CatalogEntry], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= len(entries))), "real.harlequin.catalog.normalize_catalog", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.normalize_catalog", clause="ensures:1", phase="ensures", span={"end_byte":3882,"end_column":38,"end_line":121,"start_byte":3849,"start_column":5,"start_line":121}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[CatalogEntry], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def catalog_children(catalog: CottList[CatalogEntry], parent: Option[str]) -> CottList[CatalogEntry]:
    """The direct children of parent (or the roots for Nothing) in catalog, in
catalog order. An unknown parent has no children."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    parent = _cott_normalize_f32_abi(parent, Option[str], path="$.parent")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_children.py", "65904c8a2e7aedce3de0bd0247e38a67c2a260f2a8b40811867f458c70c6f5a0", "catalog_children", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_children")
        _result = _implementation(catalog, parent)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_children"
        if _error.span is None:
            _error.span = {"end_byte":4199,"end_column":1,"end_line":135,"start_byte":3900,"start_column":1,"start_line":125}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_children", phase="implementation-call", span={"end_byte":4199,"end_column":1,"end_line":135,"start_byte":3900,"start_column":1,"start_line":125}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_children", phase="implementation-call", span={"end_byte":4199,"end_column":1,"end_line":135,"start_byte":3900,"start_column":1,"start_line":125}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[CatalogEntry], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= len(catalog))), "real.harlequin.catalog.catalog_children", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_children", clause="ensures:1", phase="ensures", span={"end_byte":4181,"end_column":38,"end_line":131,"start_byte":4148,"start_column":5,"start_line":131}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[CatalogEntry], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def replace_children(catalog: CottList[CatalogEntry], parent: str, children: CottList[CatalogEntry]) -> CottList[CatalogEntry]:
    """Replace the whole subtree below parent with children sorted by label
(case-insensitive, then exact; Harlequin sorts loaded siblings
alphabetically), keeping each child's own subtree order, and mark parent
loaded and expandable. A child is kept only when its parent is parent or a
kept child appearing earlier, and its id is new (not an id outside the
replaced subtree and not repeated); depth is recomputed. An unknown parent
returns catalog unchanged."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    parent = _cott_normalize_f32_abi(parent, str, path="$.parent")
    children = _cott_normalize_f32_abi(children, CottList[CatalogEntry], path="$.children")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/replace_children.py", "081e028b11e3427c6830c7dab87333d8c019d7241ff619d480e52f53f4924426", "replace_children", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.replace_children")
        _result = _implementation(catalog, parent, children)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.replace_children"
        if _error.span is None:
            _error.span = {"end_byte":4832,"end_column":1,"end_line":148,"start_byte":4199,"start_column":1,"start_line":135}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.replace_children", phase="implementation-call", span={"end_byte":4832,"end_column":1,"end_line":148,"start_byte":4199,"start_column":1,"start_line":135}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.replace_children", phase="implementation-call", span={"end_byte":4832,"end_column":1,"end_line":148,"start_byte":4199,"start_column":1,"start_line":135}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[CatalogEntry], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[CatalogEntry], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def visible_entries(catalog: CottList[CatalogEntry], tree: TreeState) -> CottList[CatalogEntry]:
    """The rows the tree shows: roots, and below each expanded node (whose id is in
tree.expanded) its children, recursively, in pre-order. Children of a
collapsed node are hidden however deep."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    tree = _cott_normalize_f32_abi(tree, TreeState, path="$.tree")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/visible_entries.py", "a798116bf5a7fa2d8297d89aee2a6a284fba32ebfcd18e7f5d9ac1efce3a2304", "visible_entries", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.visible_entries")
        _result = _implementation(catalog, tree)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.visible_entries"
        if _error.span is None:
            _error.span = {"end_byte":5156,"end_column":1,"end_line":157,"start_byte":4832,"start_column":1,"start_line":148}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.visible_entries", phase="implementation-call", span={"end_byte":5156,"end_column":1,"end_line":157,"start_byte":4832,"start_column":1,"start_line":148}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.visible_entries", phase="implementation-call", span={"end_byte":5156,"end_column":1,"end_line":157,"start_byte":4832,"start_column":1,"start_line":148}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[CatalogEntry], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[CatalogEntry], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def move_tree_cursor(catalog: CottList[CatalogEntry], tree: TreeState, motion: TreeMotion, page_rows: U64) -> TreeState:
    """Move the cursor over visible_entries: Up/Down by one row, PageUp/PageDown by
max(page_rows, 1) rows, First to row 0, Last to the last row, Parent to the
row of the cursor entry's parent (unchanged for roots); always clamped to
the visible rows (cursor 0 when there are none). expanded and first_row are
unchanged."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    tree = _cott_normalize_f32_abi(tree, TreeState, path="$.tree")
    motion = _cott_normalize_f32_abi(motion, TreeMotion, path="$.motion")
    page_rows = _cott_normalize_f32_abi(page_rows, U64, path="$.page_rows")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/move_tree_cursor.py", "3e82c2cb91a008f87ad4b6fcf72fc8aa52d19a882e078990b13a7c5e45312988", "move_tree_cursor", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.move_tree_cursor")
        _result = _implementation(catalog, tree, motion, page_rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.move_tree_cursor"
        if _error.span is None:
            _error.span = {"end_byte":5736,"end_column":1,"end_line":171,"start_byte":5156,"start_column":1,"start_line":157}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.move_tree_cursor", phase="implementation-call", span={"end_byte":5736,"end_column":1,"end_line":171,"start_byte":5156,"start_column":1,"start_line":157}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.move_tree_cursor", phase="implementation-call", span={"end_byte":5736,"end_column":1,"end_line":171,"start_byte":5156,"start_column":1,"start_line":157}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TreeState, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).expanded == (tree).expanded)), "real.harlequin.catalog.move_tree_cursor", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.move_tree_cursor", clause="ensures:1", phase="ensures", span={"end_byte":5671,"end_column":45,"end_line":166,"start_byte":5631,"start_column":5,"start_line":166}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).first_row == (tree).first_row)), "real.harlequin.catalog.move_tree_cursor", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.move_tree_cursor", clause="ensures:2", phase="ensures", span={"end_byte":5718,"end_column":47,"end_line":167,"start_byte":5676,"start_column":5,"start_line":167}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TreeState, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def toggle_tree_node(catalog: CottList[CatalogEntry], tree: TreeState) -> TreeToggle:
    """Expand or collapse the node under the cursor (Space in the Data Catalog, and
Enter on a node that can expand). A node that is not expandable does not
change. Expanding adds its id to expanded; when the node is not loaded,
load_children is Some(id) so the caller can fetch its children and call
replace_children. Collapsing removes the id. The cursor stays on the same
entry. With no visible rows nothing changes."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    tree = _cott_normalize_f32_abi(tree, TreeState, path="$.tree")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/toggle_tree_node.py", "01082d3b967cb6d940fc085e92299cf2cefa6562a6bfd998a6a5161405477ec8", "toggle_tree_node", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.toggle_tree_node")
        _result = _implementation(catalog, tree)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.toggle_tree_node"
        if _error.span is None:
            _error.span = {"end_byte":6338,"end_column":1,"end_line":185,"start_byte":5736,"start_column":1,"start_line":171}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.toggle_tree_node", phase="implementation-call", span={"end_byte":6338,"end_column":1,"end_line":185,"start_byte":5736,"start_column":1,"start_line":171}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.toggle_tree_node", phase="implementation-call", span={"end_byte":6338,"end_column":1,"end_line":185,"start_byte":5736,"start_column":1,"start_line":171}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TreeToggle, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((((_result).tree).cursor == (tree).cursor)), "real.harlequin.catalog.toggle_tree_node", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.toggle_tree_node", clause="ensures:1", phase="ensures", span={"end_byte":6320,"end_column":46,"end_line":181,"start_byte":6279,"start_column":5,"start_line":181}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TreeToggle, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def tree_cursor_entry(catalog: CottList[CatalogEntry], tree: TreeState) -> Option[CatalogEntry]:
    """The visible entry under the cursor, if any."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    tree = _cott_normalize_f32_abi(tree, TreeState, path="$.tree")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/tree_cursor_entry.py", "d7879e1d33f1498c92418d629a5f592dc746ff63b7deb82c2b30b3fc6d49ba0d", "tree_cursor_entry", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.tree_cursor_entry")
        _result = _implementation(catalog, tree)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.tree_cursor_entry"
        if _error.span is None:
            _error.span = {"end_byte":6515,"end_column":1,"end_line":192,"start_byte":6338,"start_column":1,"start_line":185}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.tree_cursor_entry", phase="implementation-call", span={"end_byte":6515,"end_column":1,"end_line":192,"start_byte":6338,"start_column":1,"start_line":185}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.tree_cursor_entry", phase="implementation-call", span={"end_byte":6515,"end_column":1,"end_line":192,"start_byte":6338,"start_column":1,"start_line":185}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[CatalogEntry], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[CatalogEntry], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def render_tree(catalog: CottList[CatalogEntry], tree: TreeState, width: U64, height: U64, focused: bool) -> TreeFrame:
    """Draw the visible rows into width x height cells. first_row is tree.first_row
moved minimally so the cursor row is within [first_row, first_row + height).
Each drawn row is one line of three spans: an indent-and-expander span
styled "class:hq.tree.guide" holding two spaces per depth level followed by
"▼ " for an expanded node, "▶ " for an expandable collapsed node, or "  "
for a leaf; a label span styled "class:hq.tree.label"; and, when type_label
is not "", a type span " " + type_label styled "class:hq.tree.type". When
focused, " class:hq.cursor" is appended to the label span's style of the
cursor row. Each line is cut at width cells (wcwidth). An empty catalog draws
no lines; width or height 0 draws no lines."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    tree = _cott_normalize_f32_abi(tree, TreeState, path="$.tree")
    width = _cott_normalize_f32_abi(width, U64, path="$.width")
    height = _cott_normalize_f32_abi(height, U64, path="$.height")
    focused = _cott_normalize_f32_abi(focused, bool, path="$.focused")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/render_tree.py", "ab2c8c7d5766f9c1142396714ff7b1fb71d437e455f407dc29945b3ca78c9823", "render_tree", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.render_tree")
        _result = _implementation(catalog, tree, width, height, focused)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.render_tree"
        if _error.span is None:
            _error.span = {"end_byte":7471,"end_column":1,"end_line":210,"start_byte":6515,"start_column":1,"start_line":192}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.render_tree", phase="implementation-call", span={"end_byte":7471,"end_column":1,"end_line":210,"start_byte":6515,"start_column":1,"start_line":192}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.render_tree", phase="implementation-call", span={"end_byte":7471,"end_column":1,"end_line":210,"start_byte":6515,"start_column":1,"start_line":192}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TreeFrame, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).lines) <= height)), "real.harlequin.catalog.render_tree", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.render_tree", clause="ensures:1", phase="ensures", span={"end_byte":7453,"end_column":39,"end_line":206,"start_byte":7419,"start_column":5,"start_line":206}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TreeFrame, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def list_directory(path: Path, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], FileTreeError]:
    """The Data Catalog's Files tree entries for the direct contents of directory
path, read lazily one level at a time like Harlequin's directory tree.
Entries are sorted directories first, then files, each group by name
(case-insensitive, then exact). Hidden entries (name starting with ".") are
included. For each: id and qualified_identifier are the absolute path,
parent is the given parent, depth the given depth, label the file name,
type_label "dir" for directories and "" for files, kind Directory or File,
query_name the path quoted with single quotes (a ' inside doubled),
expandable true only for directories, loaded false. A path that is not a
directory is NotADirectory(path); an unreadable directory is
Unreadable(path, message)."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    parent = _cott_normalize_f32_abi(parent, Option[str], path="$.parent")
    depth = _cott_normalize_f32_abi(depth, U64, path="$.depth")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/list_directory.py", "35f4d879083397edf606c3afc97391f4af146be2221197ac4ee537109ef245e4", "list_directory", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.list_directory")
        _result = _implementation(path, parent, depth)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.list_directory"
        if _error.span is None:
            _error.span = {"end_byte":8522,"end_column":1,"end_line":232,"start_byte":7471,"start_column":1,"start_line":210}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.list_directory", phase="implementation-call", span={"end_byte":8522,"end_column":1,"end_line":232,"start_byte":7471,"start_column":1,"start_line":210}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.list_directory", phase="implementation-call", span={"end_byte":8522,"end_column":1,"end_line":232,"start_byte":7471,"start_column":1,"start_line":210}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[CatalogEntry], FileTreeError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.list_directory", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (FileTreeError_NotADirectory, FileTreeError_Unreadable,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.list_directory", phase="error", span={"end_byte":8522,"end_column":1,"end_line":232,"start_byte":7471,"start_column":1,"start_line":210}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.list_directory", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.catalog.list_directory", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is FileTreeError_NotADirectory:
            _cott_contract_condition(True, "real.harlequin.catalog.list_directory", "error:2")
        if type(_result) is Err and type(_result.error) is FileTreeError_Unreadable:
            _cott_contract_condition(True, "real.harlequin.catalog.list_directory", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                entries = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.catalog.list_directory", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.catalog.list_directory", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.list_directory", clause="ensures:1", phase="ensures", span={"end_byte":8421,"end_column":39,"end_line":225,"start_byte":8387,"start_column":5,"start_line":225}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogEntry], FileTreeError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def list_s3(target: str, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], S3Error]:
    """The Data Catalog's S3 tree entries, listed lazily with boto3's default
credential and region chain (client("s3")). target is what --show-s3 was
given, or an "s3://bucket/prefix/" id being expanded:
- "all": every bucket from list_buckets, as roots (kind Bucket, id
  "s3://<bucket>", label the bucket name, type_label "bkt").
- a bucket name, "s3://bucket" or "s3://bucket/prefix/": the objects and
  common prefixes directly under that prefix (list_objects_v2 with
  Delimiter "/" and all pages): prefixes first as kind Prefix, type_label
  "dir", id "s3://bucket/<prefix>", label the last path segment with its
  trailing "/"; then objects as kind Object, type_label "", id
  "s3://bucket/<key>", label the last key segment. A bare bucket name given
  at the root yields the bucket itself as the single root, expandable and
  not loaded.
query_name and qualified_identifier are the id quoted with single quotes
and the plain id respectively. parent and depth are as given. Missing boto3
credentials or an unimportable SDK is Unavailable(message); an access
refusal is AccessDenied(target); other failures are Failed(target, message)
without credentials in message."""
    target = _cott_normalize_f32_abi(target, str, path="$.target")
    parent = _cott_normalize_f32_abi(parent, Option[str], path="$.parent")
    depth = _cott_normalize_f32_abi(depth, U64, path="$.depth")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/list_s3.py", "11b9b4cf319428499d143f4a257610c4ed2f5da6e4551e677dfff6540bc6f34c", "list_s3", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.list_s3")
        _result = _implementation(target, parent, depth)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.list_s3"
        if _error.span is None:
            _error.span = {"end_byte":10029,"end_column":1,"end_line":262,"start_byte":8522,"start_column":1,"start_line":232}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.list_s3", phase="implementation-call", span={"end_byte":10029,"end_column":1,"end_line":262,"start_byte":8522,"start_column":1,"start_line":232}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.list_s3", phase="implementation-call", span={"end_byte":10029,"end_column":1,"end_line":262,"start_byte":8522,"start_column":1,"start_line":232}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[CottList[CatalogEntry], S3Error], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.catalog.list_s3", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (S3Error_Unavailable, S3Error_AccessDenied, S3Error_Failed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.catalog.list_s3", phase="error", span={"end_byte":10029,"end_column":1,"end_line":262,"start_byte":8522,"start_column":1,"start_line":232}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.catalog.list_s3", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.catalog.list_s3", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is S3Error_Unavailable:
            _cott_contract_condition(True, "real.harlequin.catalog.list_s3", "error:2")
        if type(_result) is Err and type(_result.error) is S3Error_AccessDenied:
            _cott_contract_condition(True, "real.harlequin.catalog.list_s3", "error:3")
        if type(_result) is Err and type(_result.error) is S3Error_Failed:
            _cott_contract_condition(True, "real.harlequin.catalog.list_s3", "error:4")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                entries = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.catalog.list_s3", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.catalog.list_s3", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.list_s3", clause="ensures:1", phase="ensures", span={"end_byte":9917,"end_column":39,"end_line":254,"start_byte":9883,"start_column":5,"start_line":254}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[CatalogEntry], S3Error], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def builtin_completions() -> CottList[Completion]:
    """Harlequin's adapter-independent completions, in this order, value equal to
label and no context. Keywords (type_label "kw", priority 100): alter, and,
as, between, by, cascade, case, column, copy, create, cross, current,
database, delete, distinct, drop, end, except, exclude, exists, false,
filter, following, from, full, function, grant, group, having, if, ilike,
inner, insert, intersect, join, lateral, left, like, limit, merge, natural,
not, offset, on, or, order, outer, over, owner, partition, preceding,
qualify, range, rename, replace, restrict, revoke, right, row, rows, schema,
select, sequence, set, similar, table, temp, temporary, then, to, top, true,
truncate, unbounded, union, update, using, view, when, where, with. Scalar
functions (type_label "fn", priority 200): abs, ceil, concat, floor, left,
lower, ltrim, regexp_extract, regexp_replace, replace, right, round, rtrim,
sqrt. Aggregates (type_label "agg", priority 200): avg, bool_and, bool_or,
count, max, min, sum."""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/builtin_completions.py", "579df547d14086ff362433f7355ee154a21db2c84b9efcf4c4280223d0d3b374", "builtin_completions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.builtin_completions")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.builtin_completions"
        if _error.span is None:
            _error.span = {"end_byte":11188,"end_column":1,"end_line":284,"start_byte":10029,"start_column":1,"start_line":262}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.builtin_completions", phase="implementation-call", span={"end_byte":11188,"end_column":1,"end_line":284,"start_byte":10029,"start_column":1,"start_line":262}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.builtin_completions", phase="implementation-call", span={"end_byte":11188,"end_column":1,"end_line":284,"start_byte":10029,"start_column":1,"start_line":262}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[Completion], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 102)), "real.harlequin.catalog.builtin_completions", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.builtin_completions", clause="ensures:1", phase="ensures", span={"end_byte":11170,"end_column":30,"end_line":280,"start_byte":11145,"start_column":5,"start_line":280}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Completion], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def catalog_completions(catalog: CottList[CatalogEntry]) -> CottList[Completion]:
    """One Completion per catalog entry of kind Database, Schema, Table, View,
TemporaryTable or Column, in catalog order: label and value are the entry
label (completing a catalog name inserts its label, not its query_name),
type_label the entry's type_label, priority 500 + depth, and context the
parent entry's label casefolded (Nothing for roots)."""
    catalog = _cott_normalize_f32_abi(catalog, CottList[CatalogEntry], path="$.catalog")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/catalog_completions.py", "31fa0fc75420601c0a7ee9cff5901263963b6b7e1ed8977bd31c1baefac3a115", "catalog_completions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.catalog_completions")
        _result = _implementation(catalog)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.catalog_completions"
        if _error.span is None:
            _error.span = {"end_byte":11702,"end_column":1,"end_line":297,"start_byte":11188,"start_column":1,"start_line":284}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.catalog_completions", phase="implementation-call", span={"end_byte":11702,"end_column":1,"end_line":297,"start_byte":11188,"start_column":1,"start_line":284}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.catalog_completions", phase="implementation-call", span={"end_byte":11702,"end_column":1,"end_line":297,"start_byte":11188,"start_column":1,"start_line":284}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[Completion], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= len(catalog))), "real.harlequin.catalog.catalog_completions", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.catalog_completions", clause="ensures:1", phase="ensures", span={"end_byte":11684,"end_column":38,"end_line":293,"start_byte":11651,"start_column":5,"start_line":293}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Completion], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def buffer_identifiers(text: str) -> CottList[str]:
    """The identifiers written in an editor buffer, for "buf" completions: every
maximal run of letters, digits, "_" and "$" that does not start with a
digit, and every double-quoted, backtick-quoted or bracketed name with its
quotes removed, skipping text inside single-quoted strings and comments
(-- to end of line, /* ... */). Unquoted words that are builtin_completions
keywords (compared case-insensitively) are not identifiers. Names are
deduplicated case-insensitively keeping the first spelling, in order of
first appearance."""
    text = _cott_normalize_f32_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/buffer_identifiers.py", "9694338e2b57680e1ed8ce754230e94e78d0a6dc3d163945119c686afa46dceb", "buffer_identifiers", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.buffer_identifiers")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.buffer_identifiers"
        if _error.span is None:
            _error.span = {"end_byte":12346,"end_column":1,"end_line":311,"start_byte":11702,"start_column":1,"start_line":297}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.buffer_identifiers", phase="implementation-call", span={"end_byte":12346,"end_column":1,"end_line":311,"start_byte":11702,"start_column":1,"start_line":297}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.buffer_identifiers", phase="implementation-call", span={"end_byte":12346,"end_column":1,"end_line":311,"start_byte":11702,"start_column":1,"start_line":297}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def completion_set(completions: CottList[Completion]) -> Opaque[Literal["harlequin.completions"]]:
    """The CompletionSet holding completions in order; its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
    completions = _cott_normalize_f32_abi(completions, CottList[Completion], path="$.completions")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/completion_set.py", "518a3d9e2e53a64d0a72268afd5f0c6594814711357deca6141a3b91e3956f58", "completion_set", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.completion_set")
        _result = _implementation(completions)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.completion_set"
        if _error.span is None:
            _error.span = {"end_byte":12812,"end_column":1,"end_line":321,"start_byte":12346,"start_column":1,"start_line":311}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.completion_set", phase="implementation-call", span={"end_byte":12812,"end_column":1,"end_line":321,"start_byte":12346,"start_column":1,"start_line":311}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.completion_set", phase="implementation-call", span={"end_byte":12812,"end_column":1,"end_line":321,"start_byte":12346,"start_column":1,"start_line":311}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Opaque[Literal["harlequin.completions"]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Opaque[Literal["harlequin.completions"]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def join_completion_sets(first: Opaque[Literal["harlequin.completions"]], second: Opaque[Literal["harlequin.completions"]]) -> Opaque[Literal["harlequin.completions"]]:
    """The CompletionSet holding the candidates of first followed by those of
second; each set's its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
    first = _cott_normalize_f32_abi(first, Opaque[Literal["harlequin.completions"]], path="$.first")
    second = _cott_normalize_f32_abi(second, Opaque[Literal["harlequin.completions"]], path="$.second")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/join_completion_sets.py", "3b4250d247a5996e3559f695f217bb010be1b6627c360b1c2c4891e056ca4c51", "join_completion_sets", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.join_completion_sets")
        _result = _implementation(first, second)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.join_completion_sets"
        if _error.span is None:
            _error.span = {"end_byte":13344,"end_column":1,"end_line":332,"start_byte":12812,"start_column":1,"start_line":321}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.join_completion_sets", phase="implementation-call", span={"end_byte":13344,"end_column":1,"end_line":332,"start_byte":12812,"start_column":1,"start_line":321}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.join_completion_sets", phase="implementation-call", span={"end_byte":13344,"end_column":1,"end_line":332,"start_byte":12812,"start_column":1,"start_line":321}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Opaque[Literal["harlequin.completions"]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Opaque[Literal["harlequin.completions"]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def complete(candidates: Opaque[Literal["harlequin.completions"]], identifiers: CottList[str], prefix: str, limit: U64) -> CottList[Completion]:
    """Harlequin's completion menu for the word before the cursor. candidates
(a CompletionSet; its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions") holds builtin_completions, then the adapter's
completions, then catalog_completions; identifiers are buffer_identifiers of the active
buffer, each a Completion(label, value = identifier, "buf", 400, Nothing).
Matching is case-insensitive via casefold().
Member completion: when prefix contains ".", ":" or "::", the context is
the segment before the last separator with quote characters (', ", `)
trimmed and casefolded, and the member text is the part after it; only
candidates whose context equals that context are considered, and the
returned label and value are the prefix up to and including the separator
followed by the candidate label (a leading quote typed in the member text
is kept). An unquoted member text starting with a digit returns [].
Word completion otherwise: a prefix starting with a digit, or an empty
prefix, returns [].
Candidates are ranked: exact matches (label equals the text), then prefix
matches (label starts with the text), each group ordered by priority then
label casefolded; buffer identifiers equal to the typed prefix are dropped.
When exact plus prefix matches are fewer than 20 and the text has at least
two characters, fuzzy matches follow: the first character must match at the
start of the label or after "_", and the remaining characters must appear in
order; fuzzy matches are ordered by shortest matched span, then earliest
start, then shortest label. Within the final list, candidates whose type_label
is "buf" come first (stable), then duplicates of (label, type_label) are
removed keeping the first, and at most limit are returned."""
    candidates = _cott_normalize_f32_abi(candidates, Opaque[Literal["harlequin.completions"]], path="$.candidates")
    identifiers = _cott_normalize_f32_abi(identifiers, CottList[str], path="$.identifiers")
    prefix = _cott_normalize_f32_abi(prefix, str, path="$.prefix")
    limit = _cott_normalize_f32_abi(limit, U64, path="$.limit")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/catalog/complete.py", "70d0c6737fea1444e66acbec126e8d188d3dcc49c8ef2abf5c85a0a84f23ddc5", "complete", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.catalog.complete")
        _result = _implementation(candidates, identifiers, prefix, limit)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.catalog.complete"
        if _error.span is None:
            _error.span = {"end_byte":15598,"end_column":1,"end_line":367,"start_byte":13344,"start_column":1,"start_line":332}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.catalog.complete", phase="implementation-call", span={"end_byte":15598,"end_column":1,"end_line":367,"start_byte":13344,"start_column":1,"start_line":332}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.catalog.complete", phase="implementation-call", span={"end_byte":15598,"end_column":1,"end_line":367,"start_byte":13344,"start_column":1,"start_line":332}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[Completion], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) <= limit)), "real.harlequin.catalog.complete", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.catalog.complete", clause="ensures:1", phase="ensures", span={"end_byte":15580,"end_column":32,"end_line":363,"start_byte":15553,"start_column":5,"start_line":363}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Completion], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["CatalogEntry", "CatalogKind", "CatalogKind_Bucket", "CatalogKind_Column", "CatalogKind_Database", "CatalogKind_Directory", "CatalogKind_File", "CatalogKind_Object", "CatalogKind_Other", "CatalogKind_Prefix", "CatalogKind_Schema", "CatalogKind_Table", "CatalogKind_TemporaryTable", "CatalogKind_View", "Completion", "CompletionSet", "FileTreeError", "FileTreeError_NotADirectory", "FileTreeError_Unreadable", "S3Error", "S3Error_AccessDenied", "S3Error_Failed", "S3Error_Unavailable", "TreeFrame", "TreeMotion", "TreeMotion_Down", "TreeMotion_First", "TreeMotion_Last", "TreeMotion_PageDown", "TreeMotion_PageUp", "TreeMotion_Parent", "TreeMotion_Up", "TreeState", "TreeToggle", "buffer_identifiers", "builtin_completions", "catalog_children", "catalog_completions", "complete", "completion_set", "join_completion_sets", "list_directory", "list_s3", "move_tree_cursor", "normalize_catalog", "render_tree", "replace_children", "toggle_tree_node", "tree_cursor_entry", "visible_entries"]
