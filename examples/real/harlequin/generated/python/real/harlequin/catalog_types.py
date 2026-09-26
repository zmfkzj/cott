from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.style_types import StyledLine

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Database:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Schema:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Table:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_View:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_TemporaryTable:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Column:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Directory:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_File:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Bucket:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Prefix:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Object:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogKind_Other:
    pass

CatalogKind: TypeAlias = Union[CatalogKind_Database, CatalogKind_Schema, CatalogKind_Table, CatalogKind_View, CatalogKind_TemporaryTable, CatalogKind_Column, CatalogKind_Directory, CatalogKind_File, CatalogKind_Bucket, CatalogKind_Prefix, CatalogKind_Object, CatalogKind_Other]

"""One node of a Data Catalog tree (database objects, local files or S3 objects).
id is unique within its catalog: the qualified_identifier for database
objects, the absolute path for files and directories, and "s3://bucket/key"
for S3 objects. parent is the parent's id (Nothing for a root). depth is 0 for
roots. label is what the tree shows, type_label the short type shown after it
(for example "db", "sch", "t", "v", "##", "s"; "" for none). query_name is the
text Insert Name puts into the editor (a quoted identifier for database
objects, the quoted path for files and "s3://bucket/key" for S3).
qualified_identifier is the fully qualified quoted identifier (for database
objects) or path/URI. expandable says the node can have children; loaded says
its children are present in the catalog."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogEntry:
    __hash__ = None
    id: str
    parent: Option[str]
    depth: U64
    label: str
    type_label: str
    kind: CatalogKind
    qualified_identifier: str
    query_name: str
    expandable: bool
    loaded: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "parent", _cott_validate_abi(self.parent, Option[str], path="$.parent"))
        if not _cott_validated_construction():
            object.__setattr__(self, "depth", _cott_validate_abi(self.depth, U64, path="$.depth"))
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, str, path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "type_label", _cott_validate_abi(self.type_label, str, path="$.type_label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, CatalogKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "qualified_identifier", _cott_validate_abi(self.qualified_identifier, str, path="$.qualified_identifier"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query_name", _cott_validate_abi(self.query_name, str, path="$.query_name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expandable", _cott_validate_abi(self.expandable, bool, path="$.expandable"))
        if not _cott_validated_construction():
            object.__setattr__(self, "loaded", _cott_validate_abi(self.loaded, bool, path="$.loaded"))

"""Where the tree cursor is and what is expanded. expanded lists the ids of
expanded nodes (order irrelevant, no duplicates); cursor is an index into the
visible rows; first_row is the scroll position."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeState:
    __hash__ = None
    expanded: CottList[str]
    cursor: U64
    first_row: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "expanded", _cott_validate_abi(self.expanded, CottList[str], path="$.expanded"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_row", _cott_validate_abi(self.first_row, U64, path="$.first_row"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_Up:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_Down:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_PageUp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_PageDown:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_First:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_Last:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeMotion_Parent:
    pass

TreeMotion: TypeAlias = Union[TreeMotion_Up, TreeMotion_Down, TreeMotion_PageUp, TreeMotion_PageDown, TreeMotion_First, TreeMotion_Last, TreeMotion_Parent]

"""The result of toggling or selecting the node under the cursor: the new tree state,
and the id of a node whose children must be loaded before it can be shown
expanded (Nothing when none)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeToggle:
    __hash__ = None
    tree: TreeState
    load_children: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "tree", _cott_validate_abi(self.tree, TreeState, path="$.tree"))
        if not _cott_validated_construction():
            object.__setattr__(self, "load_children", _cott_validate_abi(self.load_children, Option[str], path="$.load_children"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TreeFrame:
    __hash__ = None
    lines: CottList[StyledLine]
    first_row: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "lines", _cott_validate_abi(self.lines, CottList[StyledLine], path="$.lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "first_row", _cott_validate_abi(self.first_row, U64, path="$.first_row"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileTreeError_NotADirectory:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FileTreeError_Unreadable:
    __hash__ = None
    path: Path
    message: str

FileTreeError: TypeAlias = Union[FileTreeError_NotADirectory, FileTreeError_Unreadable]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class S3Error_Unavailable:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class S3Error_AccessDenied:
    __hash__ = None
    target: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class S3Error_Failed:
    __hash__ = None
    target: str
    message: str

S3Error: TypeAlias = Union[S3Error_Unavailable, S3Error_AccessDenied, S3Error_Failed]

"""One completion candidate: label is what the menu shows and value what is
inserted; type_label is the short kind shown beside it ("kw", "fn", "agg",
"type", "set", "pragma", "t", "v", "db", "sch", a column type, ...); priority
orders candidates (lower first); context, when present, is the schema or parent
the candidate belongs to."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Completion:
    __hash__ = None
    label: str
    value: str
    type_label: str
    priority: I64
    context: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, str, path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not _cott_validated_construction():
            object.__setattr__(self, "type_label", _cott_validate_abi(self.type_label, str, path="$.type_label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "priority", _cott_validate_abi(self.priority, I64, path="$.priority"))
        if not _cott_validated_construction():
            object.__setattr__(self, "context", _cott_validate_abi(self.context, Option[str], path="$.context"))

"""An ordered, immutable collection of completion candidates of any size, passed
as one handle so that thousands of adapter candidates never cross a facade as a
list. The payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order (tag "harlequin.completions")."""
CompletionSet: TypeAlias = Opaque[Literal["harlequin.completions"]]

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
"""The direct children of parent (or the roots for Nothing) in catalog, in
catalog order. An unknown parent has no children."""
"""Replace the whole subtree below parent with children sorted by label
(case-insensitive, then exact; Harlequin sorts loaded siblings
alphabetically), keeping each child's own subtree order, and mark parent
loaded and expandable. A child is kept only when its parent is parent or a
kept child appearing earlier, and its id is new (not an id outside the
replaced subtree and not repeated); depth is recomputed. An unknown parent
returns catalog unchanged."""
"""The rows the tree shows: roots, and below each expanded node (whose id is in
tree.expanded) its children, recursively, in pre-order. Children of a
collapsed node are hidden however deep."""
"""Move the cursor over visible_entries: Up/Down by one row, PageUp/PageDown by
max(page_rows, 1) rows, First to row 0, Last to the last row, Parent to the
row of the cursor entry's parent (unchanged for roots); always clamped to
the visible rows (cursor 0 when there are none). expanded and first_row are
unchanged."""
"""Expand or collapse the node under the cursor (Space in the Data Catalog, and
Enter on a node that can expand). A node that is not expandable does not
change. Expanding adds its id to expanded; when the node is not loaded,
load_children is Some(id) so the caller can fetch its children and call
replace_children. Collapsing removes the id. The cursor stays on the same
entry. With no visible rows nothing changes."""
"""The visible entry under the cursor, if any."""
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
"""One Completion per catalog entry of kind Database, Schema, Table, View,
TemporaryTable or Column, in catalog order: label and value are the entry
label (completing a catalog name inserts its label, not its query_name),
type_label the entry's type_label, priority 500 + depth, and context the
parent entry's label casefolded (Nothing for roots)."""
"""The identifiers written in an editor buffer, for "buf" completions: every
maximal run of letters, digits, "_" and "$" that does not start with a
digit, and every double-quoted, backtick-quoted or bracketed name with its
quotes removed, skipping text inside single-quoted strings and comments
(-- to end of line, /* ... */). Unquoted words that are builtin_completions
keywords (compared case-insensitively) are not identifiers. Names are
deduplicated case-insensitively keeping the first spelling, in order of
first appearance."""
"""The CompletionSet holding completions in order; its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
"""The CompletionSet holding the candidates of first followed by those of
second; each set's its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
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
__all__ = ["CatalogEntry", "CatalogKind", "CatalogKind_Bucket", "CatalogKind_Column", "CatalogKind_Database", "CatalogKind_Directory", "CatalogKind_File", "CatalogKind_Object", "CatalogKind_Other", "CatalogKind_Prefix", "CatalogKind_Schema", "CatalogKind_Table", "CatalogKind_TemporaryTable", "CatalogKind_View", "Completion", "CompletionSet", "FileTreeError", "FileTreeError_NotADirectory", "FileTreeError_Unreadable", "S3Error", "S3Error_AccessDenied", "S3Error_Failed", "S3Error_Unavailable", "TreeFrame", "TreeMotion", "TreeMotion_Down", "TreeMotion_First", "TreeMotion_Last", "TreeMotion_PageDown", "TreeMotion_PageUp", "TreeMotion_Parent", "TreeMotion_Up", "TreeState", "TreeToggle"]
