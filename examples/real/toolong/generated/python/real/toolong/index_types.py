from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import FileIndex, FileTimestamps, LineLocation, MergedIndex, TabIndex

"""The index of a single file before its line breaks are scanned. Toolong's
backwards scan always records the content size itself as a break before
any LF offset, so for a non-empty file breaks is an opaque tuple containing
size; an empty file has no breaks. scan_start is size and scanned_size is 0."""
"""Record one batch of a backwards scan: scan_start becomes position (the
offset the scan has reached) and breaks becomes the ascending sort of the
existing breaks followed by the new ones (duplicates kept).
scanned_size is unchanged."""
"""Finish (or stop) the backwards scan: scanned_size becomes the larger of
its current value and size, scan_start becomes position (0 when the whole
file was scanned, the last reached offset when the scan was cancelled).
breaks are unchanged."""
"""Record LF offsets read while tailing: they are appended in the given order
without sorting, and scanned_size becomes the larger of its current value
and size. scan_start is unchanged."""
"""Toolong's displayed line count of a single file: the number of breaks, but
at least 1."""
"""Toolong's merge of several files by timestamp. File i of files is file
index i of the merged view.

breaks: for an opened file with at least one entry, the end offsets of its
entries in order followed by its size; otherwise an empty list. breaks has
one element per file.

lines: for each opened file in order, one MergedLine(seconds, line, file)
per entry in entry order, after back-filling a missing header timestamp:
scanning the file's entries from the first, the first entry with non-zero
seconds among the first twelve entries (positions 0 to 11) gives its
seconds to every earlier entry of that file; when none of them has
non-zero seconds nothing is back-filled. Entries that still have 0.0
seconds keep it (they sort before every timestamped line). When complete
is true, the concatenated lines are stably sorted by (seconds, line), so
equal keys keep file order; when complete is false (a cancelled merge) they
stay in file order.

scanned_size is the sum of the sizes of all files.
Each file's timestamp entries and the completed merged indexes use
opaque tuples: inspect them inside this implementation, not via a
recursively traversed facade value."""
"""Toolong's index_to_span: where displayed line number line (zero-based)
lives.

Single(file_index): the file is 0; with breaks b (length n), scan_start s
and scanned_size z: when n is 0 the span is (s, s); otherwise let i be
line clamped to at most n; i == 0 gives (s, b[0]); otherwise the span
starts at b[i - 1] and ends at b[i] when i < n, else at z - 1 (0 when z is
0). Spans of lines after the first therefore start at the preceding LF.

Merged(merged_index): when line < lines.len the file and the file's own
line number come from lines[line]; otherwise the file is 0 and the file's
own line number is line. The span is then computed exactly like Single
using that file's breaks (an empty list when the file has none), scan
start 0 and the merged scanned_size.
The index payloads are immutable tuples; unwrap and index them directly.
Do not allocate copies of all breaks or merged lines per lookup: this
callable runs once for each visible row and each search candidate."""
__all__ = []
