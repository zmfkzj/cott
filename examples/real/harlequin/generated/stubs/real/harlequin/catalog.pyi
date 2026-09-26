from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.catalog_types import CatalogEntry as CatalogEntry, CatalogKind as CatalogKind, CatalogKind_Bucket as CatalogKind_Bucket, CatalogKind_Column as CatalogKind_Column, CatalogKind_Database as CatalogKind_Database, CatalogKind_Directory as CatalogKind_Directory, CatalogKind_File as CatalogKind_File, CatalogKind_Object as CatalogKind_Object, CatalogKind_Other as CatalogKind_Other, CatalogKind_Prefix as CatalogKind_Prefix, CatalogKind_Schema as CatalogKind_Schema, CatalogKind_Table as CatalogKind_Table, CatalogKind_TemporaryTable as CatalogKind_TemporaryTable, CatalogKind_View as CatalogKind_View, Completion as Completion, CompletionSet as CompletionSet, FileTreeError as FileTreeError, FileTreeError_NotADirectory as FileTreeError_NotADirectory, FileTreeError_Unreadable as FileTreeError_Unreadable, S3Error as S3Error, S3Error_AccessDenied as S3Error_AccessDenied, S3Error_Failed as S3Error_Failed, S3Error_Unavailable as S3Error_Unavailable, TreeFrame as TreeFrame, TreeMotion as TreeMotion, TreeMotion_Down as TreeMotion_Down, TreeMotion_First as TreeMotion_First, TreeMotion_Last as TreeMotion_Last, TreeMotion_PageDown as TreeMotion_PageDown, TreeMotion_PageUp as TreeMotion_PageUp, TreeMotion_Parent as TreeMotion_Parent, TreeMotion_Up as TreeMotion_Up, TreeState as TreeState, TreeToggle as TreeToggle
from real.harlequin.style_types import StyledLine
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
def normalize_catalog(entries: CottList[CatalogEntry]) -> CottList[CatalogEntry]: ...

"""The direct children of parent (or the roots for Nothing) in catalog, in
catalog order. An unknown parent has no children."""
def catalog_children(catalog: CottList[CatalogEntry], parent: Option[str]) -> CottList[CatalogEntry]: ...

"""Replace the whole subtree below parent with children sorted by label
(case-insensitive, then exact; Harlequin sorts loaded siblings
alphabetically), keeping each child's own subtree order, and mark parent
loaded and expandable. A child is kept only when its parent is parent or a
kept child appearing earlier, and its id is new (not an id outside the
replaced subtree and not repeated); depth is recomputed. An unknown parent
returns catalog unchanged."""
def replace_children(catalog: CottList[CatalogEntry], parent: str, children: CottList[CatalogEntry]) -> CottList[CatalogEntry]: ...

"""The rows the tree shows: roots, and below each expanded node (whose id is in
tree.expanded) its children, recursively, in pre-order. Children of a
collapsed node are hidden however deep."""
def visible_entries(catalog: CottList[CatalogEntry], tree: TreeState) -> CottList[CatalogEntry]: ...

"""Move the cursor over visible_entries: Up/Down by one row, PageUp/PageDown by
max(page_rows, 1) rows, First to row 0, Last to the last row, Parent to the
row of the cursor entry's parent (unchanged for roots); always clamped to
the visible rows (cursor 0 when there are none). expanded and first_row are
unchanged."""
def move_tree_cursor(catalog: CottList[CatalogEntry], tree: TreeState, motion: TreeMotion, page_rows: U64) -> TreeState: ...

"""Expand or collapse the node under the cursor (Space in the Data Catalog, and
Enter on a node that can expand). A node that is not expandable does not
change. Expanding adds its id to expanded; when the node is not loaded,
load_children is Some(id) so the caller can fetch its children and call
replace_children. Collapsing removes the id. The cursor stays on the same
entry. With no visible rows nothing changes."""
def toggle_tree_node(catalog: CottList[CatalogEntry], tree: TreeState) -> TreeToggle: ...

"""The visible entry under the cursor, if any."""
def tree_cursor_entry(catalog: CottList[CatalogEntry], tree: TreeState) -> Option[CatalogEntry]: ...

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
def render_tree(catalog: CottList[CatalogEntry], tree: TreeState, width: U64, height: U64, focused: bool) -> TreeFrame: ...

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
def list_directory(path: Path, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], FileTreeError]: ...

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
def list_s3(target: str, parent: Option[str], depth: U64) -> Result[CottList[CatalogEntry], S3Error]: ...

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
def builtin_completions() -> CottList[Completion]: ...

"""One Completion per catalog entry of kind Database, Schema, Table, View,
TemporaryTable or Column, in catalog order: label and value are the entry
label (completing a catalog name inserts its label, not its query_name),
type_label the entry's type_label, priority 500 + depth, and context the
parent entry's label casefolded (Nothing for roots)."""
def catalog_completions(catalog: CottList[CatalogEntry]) -> CottList[Completion]: ...

"""The identifiers written in an editor buffer, for "buf" completions: every
maximal run of letters, digits, "_" and "$" that does not start with a
digit, and every double-quoted, backtick-quoted or bracketed name with its
quotes removed, skipping text inside single-quoted strings and comments
(-- to end of line, /* ... */). Unquoted words that are builtin_completions
keywords (compared case-insensitively) are not identifiers. Names are
deduplicated case-insensitively keeping the first spelling, in order of
first appearance."""
def buffer_identifiers(text: str) -> CottList[str]: ...

"""The CompletionSet holding completions in order; its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
def completion_set(completions: CottList[Completion]) -> Opaque[Literal["harlequin.completions"]]: ...

"""The CompletionSet holding the candidates of first followed by those of
second; each set's its payload is a Python tuple of real.harlequin.catalog_types.Completion
values in candidate order: build it with cott_runtime.Opaque(tag="harlequin.completions",
value=tuple(...)) and read it with cast(tuple[Completion, ...], handle.unwrap())
after checking handle.tag == "harlequin.completions"."""
def join_completion_sets(first: Opaque[Literal["harlequin.completions"]], second: Opaque[Literal["harlequin.completions"]]) -> Opaque[Literal["harlequin.completions"]]: ...

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
def complete(candidates: Opaque[Literal["harlequin.completions"]], identifiers: CottList[str], prefix: str, limit: U64) -> CottList[Completion]: ...

__all__ = ["CatalogEntry", "CatalogKind", "CatalogKind_Bucket", "CatalogKind_Column", "CatalogKind_Database", "CatalogKind_Directory", "CatalogKind_File", "CatalogKind_Object", "CatalogKind_Other", "CatalogKind_Prefix", "CatalogKind_Schema", "CatalogKind_Table", "CatalogKind_TemporaryTable", "CatalogKind_View", "Completion", "CompletionSet", "FileTreeError", "FileTreeError_NotADirectory", "FileTreeError_Unreadable", "S3Error", "S3Error_AccessDenied", "S3Error_Failed", "S3Error_Unavailable", "TreeFrame", "TreeMotion", "TreeMotion_Down", "TreeMotion_First", "TreeMotion_Last", "TreeMotion_PageDown", "TreeMotion_PageUp", "TreeMotion_Parent", "TreeMotion_Up", "TreeState", "TreeToggle", "buffer_identifiers", "builtin_completions", "catalog_children", "catalog_completions", "complete", "completion_set", "join_completion_sets", "list_directory", "list_s3", "move_tree_cursor", "normalize_catalog", "render_tree", "replace_children", "toggle_tree_node", "tree_cursor_entry", "visible_entries"]
