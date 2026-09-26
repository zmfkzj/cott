from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.adapters_types import AdapterDescriptor
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.history_types import HarlequinPaths
from real.harlequin.keymap_types import KeyMap
from real.harlequin.results_types import NumberFormat
from real.harlequin.style_types import ThemePalette
from real.harlequin.support_types import SshTunnel

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def build_ide(settings: HarlequinSettings, context: IdeContext, keymaps: CottList[KeyMap]) -> IdeSession:
    """Build (but do not run) the IDE screen with the lock-selected prompt_toolkit,
without classes, and return its IdeSession with every key of the shared
state initialised: no connection, one blank "Tab 1" buffer, layout
real.harlequin.ide.initial_layout(), run bar
real.harlequin.ide.new_run_bar(settings.limit), no results
("empty"), empty catalogs and trees (TreeState with no expanded ids, cursor
0, first_row 0), catalog_tab "Databases", no notifications or dialog, empty
handlers, dialog_keys, on_exit and on_crash, and the services listed for
build_ide. "bound_handle" is the Ok value of
real.harlequin.keymap.bind_keymaps(real.harlequin.keymap.builtin_keymaps()
followed by keymaps, settings.keymap_names); on Err bind only the builtin
"vscode" keymap. The shipped vscode bindings all name known actions and
include Quit, so the builtin bind is Ok; extract that value rather than
fabricating an empty BoundKeySet. Check bound_handle.handle.tag ==
"harlequin.bound_keys" and store
tuple[BoundKey, ...] from bound_handle.handle.unwrap() as
S["bound"] without a copy.
Keep S["bound_handle"] for footer_hints and help_lines, so the full list
never crosses another facade boundary.
Style: prompt_toolkit.styles.Style.from_dict of
real.harlequin.style.theme_style_rules(context.palette). A StyledLine is
drawn as the fragments [(span.style, span.text), ...]; lines join with
("", "\\n").
Layout (HSplit): a VSplit of the Data Catalog (Window width
Dimension(weight=1), shown when the layout shows the Catalog pane per
real.harlequin.ide.visible_panes) framed "Data Catalog" with a tab strip
real.harlequin.ide.render_tab_bar(["Databases", "Files", "S3"] present
tabs) when Files or S3 are configured and the tree drawn by
real.harlequin.catalog.render_tree(entries, tree, width, height, focused),
and the main column (weight 3): the Query Editor framed "Query Editor" with
the buffer tab strip (render_tab_bar of the titles, shown with 2+ buffers)
and the active buffer's BufferControl (lexer
PygmentsLexer(pygments.lexers.sql.SqlLexer), line numbers, a
DynamicContainer so switching buffers swaps the control), the one-line
Run Query Bar real.harlequin.ide.render_run_bar(run_bar, the connection's
transaction_mode, descriptor.implements_cancel, real.harlequin.ide.run_label(
selected text, true), runnable = active text not blank, focused, width),
and the Results Viewer framed by real.harlequin.results.results_title of
the current result ("Query Results" when empty, "Running Query" while
loading) with a "Result N" tab strip for 2+ results and
real.harlequin.results.render_grid(grid, width, height, focused,
context.number_format) (storing the frame's first_row/first_column back into
the grid), or "Query Returned No Records" for a zero-row result. The last
row is the footer real.harlequin.ide.render_footer(
real.harlequin.keymap.footer_hints(bound_handle, focused scope), width). Editor
and results share the main column height equally. Floats: the open dialog
centred (text: real.harlequin.ide.render_text_modal; input:
real.harlequin.ide.render_input_modal; confirm:
real.harlequin.ide.render_confirm; menu:
real.harlequin.ide.render_context_menu;
export: real.harlequin.export.render_export_dialog; history:
real.harlequin.history.render_history with the local UTC offset in minutes)
and real.harlequin.ide.render_notifications(notifications, now, 60) at the
bottom right; a 0.5 s refresh_interval expires notifications.
Key dispatch: for every BoundKey, each sequence of
real.harlequin.keymap.terminal_key_sequence(key) (None: skipped) is added
to "kb" once per distinct sequence with a filter that is true when a dialog
is open (its dialog_keys entry exists) or when an installed handler exists
for the action bound to that key in the focused scope (Catalog pane:
Catalog; Editor or RunBar: Editor; Results: Results) or in the App scope
(priority bindings first). Pressing it calls the dialog's dialog_keys
function with the textual key name when a dialog is open, else the
handler. While a dialog is open every other key (Keys.Any, escape, enter,
tab, arrows, backspace, delete, home, end, pageup, pagedown) goes to the
dialog as its textual name ("escape", "enter", "tab", "up", "backspace",
"space" for " ", the character itself for printable text) with the typed
text. Unbound keys in the editor keep prompt_toolkit's default editing.
Focus: the catalog, run bar and results windows are focusable
FormattedTextControl windows; S["focus"] keeps LayoutState.focus and the
prompt_toolkit focus in step."""
    settings = _cott_normalize_f32_abi(settings, HarlequinSettings, path="$.settings")
    context = _cott_normalize_f32_abi(context, IdeContext, path="$.context")
    keymaps = _cott_normalize_f32_abi(keymaps, CottList[KeyMap], path="$.keymaps")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/build_ide.py", "041841efe03398654b37899a0c52ccb7a1207cd7f1fe3c274d9fc0ec765d4c5f", "build_ide", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.build_ide")
        _result = _implementation(settings, context, keymaps)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.build_ide"
        if _error.span is None:
            _error.span = {"end_byte":10051,"end_column":1,"end_line":171,"start_byte":5115,"start_column":1,"start_line":95}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.build_ide", phase="implementation-call", span={"end_byte":10051,"end_column":1,"end_line":171,"start_byte":5115,"start_column":1,"start_line":95}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.build_ide", phase="implementation-call", span={"end_byte":10051,"end_column":1,"end_line":171,"start_byte":5115,"start_column":1,"start_line":95}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, IdeSession, path="$.return")
    _result = _cott_wrap_async_protocol(_result, IdeSession, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def install_editor_actions(session: IdeSession) -> Unit:
    """Register the Query Editor's handlers, dialog_keys and services in the
shared state (see IdeSession) and restore the buffers. Buffers: from
real.harlequin.support.adopt_recovery(context.paths.cache_dir, time.time())
(then notify "Buffers recovered", "Recovered buffers from a session that
ended unexpectedly.", information), else
real.harlequin.support.load_buffer_cache(context.paths.buffer_cache) (an
error notifies warning "Harlequin could not load its cache."), else keep
the blank buffer; focus the cached focus_index (clamped), restoring each
buffer's text and selection. Every 60 seconds a daemon timer thread saves
the buffers with real.harlequin.support.save_buffer_cache to
cache_dir/"recovery-{pid}.json" when some buffer is nonblank and the
buffers differ from the last checkpoint.
Handlers: "new_buffer" (blank "Tab N", N = ++tab_counter, focus editor);
"close_buffer" (remove the active buffer, the next one becomes active; the
only buffer is cleared instead); "next_buffer" (cycle when 2+);
"format_buffer" (real.harlequin.sqltext.format_sql of the text; Err opens
the text dialog real.harlequin.ide.error_modal("Formatting Error", "There
was an error while formatting your file:", message); changed text keeps
the cursor offset and notifies "Formatted query.", unchanged notifies
"Query was already formatted; no changes made."); "toggle_comment"
(real.harlequin.sqltext.toggle_comment over the selection); "save_buffer"
and "load_buffer" (open the input dialog real.harlequin.ide.input_modal(
SaveFile / OpenFile, "") whose dialog_keys go through
real.harlequin.ide.input_key; Complete applies
real.harlequin.ide.apply_completions(modal,
real.harlequin.files.complete_path(value, home, cwd)); Submit expands with
real.harlequin.files.expand_path and calls
real.harlequin.files.save_text_file (notify "Editor contents saved to
{path}") or real.harlequin.files.load_text_file into the active buffer;
errors open real.harlequin.ide.error_modal("File Error", ...)); "find" (input dialog Find;
Submit selects the next case-insensitive match after the cursor,
wrapping) and "find_next" (repeat the last search); "goto_line" (input
dialog GoToLine; moves to the 1-based line, clamped); "launch_external_editor"
(prompt_toolkit.application.run_in_terminal running
real.harlequin.support.edit_externally(text,
real.harlequin.support.resolve_editor(environment)); a Some text replaces
the buffer; errors notify); "copy", "cut" (selected text through
real.harlequin.support.copy_to_clipboard, falling back to writing
real.harlequin.support.osc52_sequence to the terminal output), "paste"
(real.harlequin.support.paste_from_clipboard inserted at the cursor),
"undo", "redo" (the Buffer's own undo/redo), and every other code_editor
cursor_*, select_*, delete_*, scroll_* action as the matching prompt_toolkit
Buffer operation (select_* extends the selection). The editor Buffer gets a completer built without
classes: a local get_completions annotated
Callable[[Document, CompleteEvent], Iterable[Completion]] bound to
lambda document, complete_event: _complete(S, document, complete_event)
(the annotation types the lambda parameters), then typing.cast(Completer,
types.SimpleNamespace(get_completions=get_completions)) in
ThreadedCompleter, yielding
real.harlequin.catalog.complete(S["completions"],
real.harlequin.catalog.buffer_identifiers(text), word before cursor, 50) as
prompt_toolkit Completions (display_meta = type_label).
Services: "new_buffer", "insert_text", "selection" as documented.
on_exit: save every buffer (text, anchor, cursor) and the active index
with real.harlequin.support.save_buffer_cache(context.paths.buffer_cache,
...) even when blank, then remove this process's recovery file with
real.harlequin.support.remove_file. on_crash: save the buffers to
cache_dir/"recovered-{UTC %Y%m%dT%H%M%S}-{pid}.json".
The Python function keeps the exact signature
(session: IdeSession) -> Unit and returns cott_runtime.Unit()."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/install_editor_actions.py", "6b0568e83394200f5e2b215b47db84eec27a57b1cb3ce10106a437fe65a99c0f", "install_editor_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.install_editor_actions")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.install_editor_actions"
        if _error.span is None:
            _error.span = {"end_byte":14386,"end_column":1,"end_line":237,"start_byte":10051,"start_column":1,"start_line":171}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.install_editor_actions", phase="implementation-call", span={"end_byte":14386,"end_column":1,"end_line":237,"start_byte":10051,"start_column":1,"start_line":171}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.install_editor_actions", phase="implementation-call", span={"end_byte":14386,"end_column":1,"end_line":237,"start_byte":10051,"start_column":1,"start_line":171}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def install_query_actions(session: IdeSession) -> Unit:
    """Register query execution in the shared state (see IdeSession) and start
connecting. Connection: a daemon thread runs
real.harlequin.adapters.connect(settings.request); Ok stores the
connection, notifies "Database Connected." (or the connection's
init_message with title "Database Connected.") and starts a catalog load;
Err stores the error, sets the app result to 2 and exits the app, and an
on_exit entry prints "{title}\\n\\n{message}" of the ConnectionError to
stderr (ReadOnlyUnsupported: "Harlequin could not connect to your
database." and "The {adapter} adapter does not support read-only
connections."). With a tunnel it first notifies title "SSH tunnel" the
tunnel host, ports and warnings (warning when reused or warned, else
information).
Catalog load (service "refresh_catalog" and handler "refresh_catalog"): a
thread runs real.harlequin.adapters.load_catalog then
real.harlequin.catalog.normalize_catalog (Err opens real.harlequin.ide.error_modal("Catalog
Error", "Could not update data catalog", message)) and rebuilds
"completions" as real.harlequin.catalog.join_completion_sets of
real.harlequin.catalog.completion_set(
real.harlequin.catalog.builtin_completions()), the Ok set of
real.harlequin.adapters.adapter_completions(connection) (Err notifies
warning "Harlequin could not load completions from your adapter." and
contributes nothing) and real.harlequin.catalog.completion_set(
real.harlequin.catalog.catalog_completions(catalog)).
Handlers "run_query" and "code_editor.run_query" (and the run bar's Enter): statements =
real.harlequin.sqltext.selected_queries(text, TextRange(anchor, cursor))
of S["selection"](); nothing happens without a connection, while running,
or with no statements. Service "run_statements": leave full screen, set
running and results_state "loading", then on a daemon thread
real.harlequin.adapters.execute_statements(connection, statements,
real.harlequin.ide.effective_limit(run_bar), false); when
settings.record_history each statement is logged to
context.paths.query_log with real.harlequin.history.record_query
(program "harlequin", sql redacted with
real.harlequin.sqltext.redact_sql, status Ok for DDL/DML and results,
Error with the failure text); a HistoryError is notified once as warning
titled "Query History". Then each executed statement with a cursor is
fetched with real.harlequin.adapters.fetch_result(connection, executed,
limit, settings.viewer_max_rows) and logged with
real.harlequin.history.update_query (rows, truncated, elapsed). Results
replace "results" and "grids" (real.harlequin.results.new_grid) and focus
the Results Viewer; DDL/DML-only batches notify "{n} DDL/DML query
executed successfully in {s:.2f} seconds." ("queries" when n != 1) and
refresh the catalog; batches with results notify "{n} query executed
successfully in {s:.2f} seconds." ("queries" when n != 1); the first
failure opens real.harlequin.ide.error_modal("Query Error", failure.title, failure.message).
Handler "cancel_query" (when descriptor.implements_cancel and running):
real.harlequin.adapters.cancel_queries, then notify error "Queries
canceled."; errors open real.harlequin.ide.error_modal("Cancel Error", "Harlequin could not
cancel your queries.", message). Handlers "toggle_transaction_mode",
"commit_transaction" and "rollback_transaction" call
real.harlequin.adapters.toggle_transaction_mode (storing the returned
connection), real.harlequin.adapters.commit_transaction (notify "Transaction committed in
{s:.2f} seconds." and refresh the catalog) and real.harlequin.adapters.rollback_transaction
("Transaction rolled back in {s:.2f} seconds.") on threads; errors open
error_modal("Transaction Error", "Harlequin could not change the
transaction mode." / "Harlequin could not commit the transaction." /
"Harlequin could not roll back the transaction.", message). The run bar's
keys (focus RunBar, action-less keys) go through
real.harlequin.ide.run_bar_key; submit runs the query.
on_exit: close the connection with real.harlequin.adapters.close_connection.
The Python function keeps the exact signature
(session: IdeSession) -> Unit and returns cott_runtime.Unit()."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/install_query_actions.py", "d27e013fbfa3d502e4a3fa9721408e63ade772614e09d099b37245349c71f243", "install_query_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.install_query_actions")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.install_query_actions"
        if _error.span is None:
            _error.span = {"end_byte":18923,"end_column":1,"end_line":305,"start_byte":14386,"start_column":1,"start_line":237}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.install_query_actions", phase="implementation-call", span={"end_byte":18923,"end_column":1,"end_line":305,"start_byte":14386,"start_column":1,"start_line":237}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.install_query_actions", phase="implementation-call", span={"end_byte":18923,"end_column":1,"end_line":305,"start_byte":14386,"start_column":1,"start_line":237}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def install_catalog_actions(session: IdeSession) -> Unit:
    """Register the Data Catalog's handlers in the shared state (see IdeSession).
Tree keys of the active catalog tab: "cursor_up" and "cursor_down" map to
real.harlequin.catalog.move_tree_cursor Up and Down, and the catalog
window's unbound pageup, pagedown, home, end and left keys to PageUp,
PageDown, First, Last and Parent (page size = catalog height); "toggle_node" and "select_cursor" use real.harlequin.catalog.toggle_tree_node and,
when it asks for children, loads them on a thread with
real.harlequin.adapters.load_catalog_children (Databases),
real.harlequin.catalog.list_directory (Files, depth of the parent + 1) or
real.harlequin.catalog.list_s3 (S3), merged with
real.harlequin.catalog.replace_children; errors open real.harlequin.ide.error_modal("Catalog
Error", ...). "insert_name" inserts (and "copy_name" copies with
real.harlequin.support.copy_to_clipboard) the entry's query_name
(real.harlequin.catalog.tree_cursor_entry) through S["insert_text"].
"show_context_menu" opens real.harlequin.ide.context_menu(entry,
real.harlequin.adapters.catalog_interactions(adapter, entry)) whose keys go
through real.harlequin.ide.context_menu_key; a chosen label runs
real.harlequin.adapters.plan_interaction(adapter, entry, label, loaded
children): InsertText inserts it, InsertChildNames inserts the children's
query names joined by ", ", NewBuffer and NewBufferFromQuery open a buffer
(the latter with real.harlequin.adapters.run_scalar_query's text, failure
notifying the failure text), Execute runs sql (after a
real.harlequin.ide.confirm_key dialog when confirm is Some) on a thread
with run_scalar_query, notifies success, refreshes the catalog when
refresh, and opens real.harlequin.ide.error_modal("Data Catalog Interaction Error", "Harlequin
could not execute an interaction from your data catalog.", message) on
failure. "next_tab" / "previous_tab" switch among the
configured tabs, loading Files from settings.show_files with
list_directory(path, None, 0) and S3 from settings.show_s3 with
list_s3(target, None, 0) the first time they are shown.
The Python function keeps the exact signature
(session: IdeSession) -> Unit and returns cott_runtime.Unit()."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/install_catalog_actions.py", "a060e99f0daf8e975c4517f70fd94f574f8625b5ae55f4e4599fd4ba6dcde730", "install_catalog_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.install_catalog_actions")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.install_catalog_actions"
        if _error.span is None:
            _error.span = {"end_byte":21369,"end_column":1,"end_line":342,"start_byte":18923,"start_column":1,"start_line":305}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.install_catalog_actions", phase="implementation-call", span={"end_byte":21369,"end_column":1,"end_line":342,"start_byte":18923,"start_column":1,"start_line":305}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.install_catalog_actions", phase="implementation-call", span={"end_byte":21369,"end_column":1,"end_line":342,"start_byte":18923,"start_column":1,"start_line":305}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def install_results_actions(session: IdeSession) -> Unit:
    """Register the Results Viewer's handlers in the shared state (see
IdeSession). Motions of the current grid through
real.harlequin.results.move_grid (page size = results height): "cursor_up",
"cursor_down", "cursor_left", "cursor_right" (Up/Down/Left/Right),
"cursor_row_start"/"cursor_row_end", "cursor_column_start"/
"cursor_column_end", "cursor_next_cell"/"cursor_previous_cell",
"cursor_page_up"/"cursor_page_down", "cursor_table_start"/
"cursor_table_end", "select_all", and each "select_*" action as the same
motion with extend true. "next_tab" / "previous_tab" cycle result tabs.
"copy_selection" copies real.harlequin.results.selection_text(grid) with
real.harlequin.support.copy_to_clipboard and notifies "Selected data
copied to clipboard.". "view_cell" opens
real.harlequin.ide.cell_modal(column, text) for
real.harlequin.results.cursor_cell(grid) (nothing when Nothing); its
dialog_keys go through real.harlequin.ide.text_modal_key and Copy copies
the text. the App action "show_data_exporter" (with at least one result) opens
real.harlequin.export.new_export_dialog(settings.export_path) whose keys go
through real.harlequin.export.export_dialog_key; Export runs
real.harlequin.export.write_result(current result, request) on a thread
and notifies "Data exported to {path}." or opens real.harlequin.ide.error_modal("Export Data
Error", "Harlequin encountered an error while exporting your data.",
message).
Shared-state service callbacks must be invoked inline as
typing.cast(Callable[..., ...], shared["service_name"])(), not by assigning
the callback to a local name and calling that local (the audit treats an
assigned callable as a dynamic Cott call).
The Python function keeps the exact signature
(session: IdeSession) -> Unit and returns cott_runtime.Unit()."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/install_results_actions.py", "7e4a5b6921c1073ec22d06d9992f2da0bccd3dcffc8525e065a5457fb1ead640", "install_results_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.install_results_actions")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.install_results_actions"
        if _error.span is None:
            _error.span = {"end_byte":23387,"end_column":1,"end_line":376,"start_byte":21369,"start_column":1,"start_line":342}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.install_results_actions", phase="implementation-call", span={"end_byte":23387,"end_column":1,"end_line":376,"start_byte":21369,"start_column":1,"start_line":342}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.install_results_actions", phase="implementation-call", span={"end_byte":23387,"end_column":1,"end_line":376,"start_byte":21369,"start_column":1,"start_line":342}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def install_app_actions(session: IdeSession) -> Unit:
    """Register the App-scope handlers in the shared state (see IdeSession).
"quit": exit the application with result 0. "toggle_sidebar",
"toggle_full_screen", "focus_query_editor", "focus_results_viewer",
"focus_data_catalog", "focus_next", "focus_previous": S["focus"](action).
"help": the text dialog real.harlequin.ide.help_modal(
real.harlequin.keymap.help_lines(bound_handle)); "show_debug_info":
real.harlequin.ide.debug_modal with sections "Harlequin" (version, python,
platform), "Adapter" (descriptor fields), "Connection" (connection_id,
driver_details, transaction mode) and "Settings" (theme, keymaps, limit,
viewer_max_rows, locale); both dialogs use real.harlequin.ide.text_modal_key
for their keys (Copy copies with real.harlequin.support.copy_to_clipboard).
"show_query_history": on a thread read
real.harlequin.history.recent_queries(context.paths.query_log, the
screen's filter, 500) and open the history dialog
(real.harlequin.history.open_history_screen(connection_id or "")); its keys
go through real.harlequin.history.history_key: Reload re-reads with the new
filter, Select closes and calls S["new_buffer"](sql), Close closes; read
errors notify warning "Harlequin could not read your query history."
titled "Query History". With a tunnel, a daemon thread checks
real.harlequin.support.ssh_tunnel_alive every 5 seconds and notifies
error "The SSH tunnel to {host} closed." once when it dies."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/install_app_actions.py", "a4ed907416aeda0edbbc6f7387f2d1786646a5a84c70aa26e26faadd3c923eff", "install_app_actions", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.install_app_actions")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.install_app_actions"
        if _error.span is None:
            _error.span = {"end_byte":25019,"end_column":1,"end_line":403,"start_byte":23387,"start_column":1,"start_line":376}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.install_app_actions", phase="implementation-call", span={"end_byte":25019,"end_column":1,"end_line":403,"start_byte":23387,"start_column":1,"start_line":376}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.install_app_actions", phase="implementation-call", span={"end_byte":25019,"end_column":1,"end_line":403,"start_byte":23387,"start_column":1,"start_line":376}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_ide_app(session: IdeSession) -> I64:
    """Run the IDE's Application on the controlling terminal until it exits and
return the exit status: the application's result (0 after "quit", 2 after
a failed connection) once every S["on_exit"] callable has run in order
(each one's exception is printed to stderr and the rest still run). An
unexpected exception restores the terminal, runs every S["on_crash"]
callable, prints "Harlequin encountered an unexpected error and had to
quit." and the exception's text to stderr, and returns 1. Afterwards the
SSH tunnel of the context, when present, is closed with
real.harlequin.support.close_ssh_tunnel. Each cleanup hook is called
inline as typing.cast(Callable[[], None], raw_hook)(), never by assigning
it to a local variable and calling that variable; the audit rejects
dynamic local calls."""
    session = _cott_normalize_f32_abi(session, IdeSession, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/app/run_ide_app.py", "448170c90377fec45973a3ba99c8a6daacd3041c64c06a5f9887ec5ce05713c8", "run_ide_app", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.app.run_ide_app")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.app.run_ide_app"
        if _error.span is None:
            _error.span = {"end_byte":25952,"end_column":1,"end_line":420,"start_byte":25019,"start_column":1,"start_line":403}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.app.run_ide_app", phase="implementation-call", span={"end_byte":25952,"end_column":1,"end_line":420,"start_byte":25019,"start_column":1,"start_line":403}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.app.run_ide_app", phase="implementation-call", span={"end_byte":25952,"end_column":1,"end_line":420,"start_byte":25019,"start_column":1,"start_line":403}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, I64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["IdeContext", "IdeSession", "build_ide", "install_app_actions", "install_catalog_actions", "install_editor_actions", "install_query_actions", "install_results_actions", "run_ide_app"]
