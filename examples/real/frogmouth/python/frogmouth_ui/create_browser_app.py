from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import ClassVar, cast, final, override
from urllib.parse import urlsplit

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some, Unit
from frogmouth.application import (
    SidebarDock,
    SidebarDock_Left,
    SidebarDock_Right,
    SidebarMode,
    SidebarMode_Bookmarks,
    SidebarMode_Help,
    SidebarMode_Hidden,
    SidebarMode_History,
    toggle_sidebar,
    toggle_sidebar_dock,
)
from frogmouth.document import (
    LoadError,
    LoadError_HttpFailure,
    LoadError_InvalidEncoding,
    LoadError_InvalidLocation,
    LoadError_NetworkUnavailable,
    LoadError_NotFound,
    LoadError_PermissionDenied,
    LoadError_ReadFailure,
    LoadError_TooLarge,
    load_document,
)
from frogmouth.model import (
    BrowserState,
    Document,
    Location,
    LocationKind_Codeberg,
    LocationKind_GitHub,
    LocationKind_Local,
    LocationKind_Remote,
    StateAction,
    StateAction_AddHistory,
    StateAction_ClearHistory,
    StateAction_RemoveHistory,
    StateAction_ToggleBookmark,
)
from frogmouth.navigation import (
    NavigationError,
    NavigationError_EmptyInput,
    NavigationError_InvalidLocation,
    NavigationError_MissingBase,
    NavigationError_UnsupportedScheme,
    display_location,
    resolve_location,
)
from frogmouth.persistence import (
    StateError,
    StateError_InvalidData,
    StateError_PermissionDenied,
    load_state,
    save_state,
    update_state,
)
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Input, Label, ListItem, ListView, Markdown, MarkdownViewer
from textual.worker import Worker, WorkerState


def create_browser_app(
    initial_location: Option[str], working_directory: Path, state_path: Path
) -> App[None]:
    @dataclass(frozen=True, slots=True)
    class DocumentLoaded:
        location: Location
        push: bool
        history_index: int | None
        result: Result[Document, LoadError]

    @dataclass(frozen=True, slots=True)
    class StateLoaded:
        result: Result[BrowserState, StateError]

    @dataclass(frozen=True, slots=True)
    class StateSaved:
        state: BrowserState
        result: Result[Unit, StateError]

    class SidebarItem(ListItem):
        def __init__(
            self, label: str, location: str | None = None, *, disabled: bool = False
        ) -> None:
            super().__init__(Label(label, markup=False), disabled=disabled)
            self.location: str | None = location

    class BrowserMarkdownViewer(MarkdownViewer):
        # ponytail: pinned Textual 6.6 private hook; replace when MarkdownViewer exposes a public interception hook.
        @override
        async def _on_markdown_link_clicked(
            self, message: Markdown.LinkClicked
        ) -> None:
            return None

    def error_message(
        error: NavigationError | LoadError | StateError,
    ) -> str:
        if isinstance(error, NavigationError_EmptyInput):
            return "Enter a location."
        if isinstance(error, NavigationError_MissingBase):
            return "An anchor needs an open document."
        if isinstance(error, NavigationError_UnsupportedScheme):
            return f"Unsupported scheme: {error.scheme}"
        if isinstance(error, NavigationError_InvalidLocation):
            return f"Invalid location: {error.value}"
        if isinstance(error, LoadError_NotFound):
            return f"Document not found: {error.source}"
        if isinstance(error, LoadError_PermissionDenied):
            return f"Permission denied: {error.source}"
        if isinstance(error, LoadError_InvalidEncoding):
            return f"Document is not valid UTF-8: {error.source}"
        if isinstance(error, LoadError_TooLarge):
            return f"Document is too large: {error.source}"
        if isinstance(error, LoadError_HttpFailure):
            return f"HTTP {error.status}: {error.url}"
        if isinstance(error, LoadError_NetworkUnavailable):
            return f"Network unavailable: {error.url}"
        if isinstance(error, LoadError_InvalidLocation):
            return f"Invalid document location: {error.message}"
        if isinstance(error, LoadError_ReadFailure):
            return f"Unable to read {error.source}: {error.message}"
        if isinstance(error, StateError_PermissionDenied):
            return f"Permission denied while saving state: {error.path}"
        if isinstance(error, StateError_InvalidData):
            return f"Invalid saved state: {error.path}"
        return f"State I/O failed for {error.path}: {error.message}"

    @final
    class FrogmouthApp(App[None]):
        CSS: ClassVar[str] = """
        Screen {
            layout: vertical;
        }

        #address {
            width: 100%;
            border-bottom: tall $accent;
        }

        #main {
            width: 100%;
            height: 1fr;
        }

        #sidebar {
            width: 34;
            min-width: 18;
            max-width: 40%;
            height: 1fr;
            dock: left;
            background: $panel;
            border-right: tall $accent;
        }

        #sidebar.-right {
            border-right: none;
            border-left: tall $accent;
        }

        #sidebar.-hidden {
            display: none;
        }

        #sidebar-mode {
            width: 100%;
            padding: 1 2;
            text-style: bold;
            background: $boost;
        }

        #sidebar-list {
            width: 100%;
            height: 1fr;
            background: $panel;
        }

        #sidebar-list ListItem {
            padding: 0 1;
        }

        #wviewer {
            width: 1fr;
            height: 1fr;
        }
        """
        BINDINGS: ClassVar[list[BindingType]] = [
            Binding("f1", "help", "Help", show=True),
            Binding("h", "history", "History", show=True),
            Binding("b", "bookmarks", "Bookmarks", show=True),
            Binding("t", "toggle_toc", "TOC", show=True),
            Binding("ctrl+b", "bookmark", "Bookmark", show=True),
            Binding("delete", "delete_history", "Delete history", show=True),
            Binding("ctrl+delete", "clear_history", "Clear history", show=True),
            Binding("d", "dock_sidebar", "Dock", show=True),
            Binding("ctrl+r", "reload", "Reload", show=True),
            Binding("colon", "focus_address", "Address", show=True),
            Binding("alt+left", "history_back", "Back", show=True),
            Binding("alt+right", "forward", "Forward", show=True),
            Binding("j,s", "scroll_down", "Line down", show=True),
            Binding("k,w", "scroll_up", "Line up", show=True),
            Binding("space", "page_down", "Page down", show=True),
            Binding("q", "quit", "Quit", show=True),
        ]

        def __init__(
            self,
            requested_location: Option[str],
            cwd: Path,
            persistence_path: Path,
        ) -> None:
            super().__init__()
            self.title = "Frogmouth"
            self._requested_location: Option[str] = requested_location
            self._working_directory: Path = cwd
            self._state_path: Path = persistence_path
            self._current_location: Location | None = None
            self._back_forward: list[Location] = []
            self._back_forward_index: int = -1
            self._browser_state: BrowserState = BrowserState(
                history=CottList(values=()), bookmarks=CottList(values=())
            )
            self._sidebar_mode: SidebarMode = SidebarMode_Hidden()
            self._sidebar_dock: SidebarDock = SidebarDock_Left()
            self._document_worker: Worker[DocumentLoaded] | None = None
            self._state_worker: Worker[StateLoaded] | None = None
            self._save_worker: Worker[StateSaved] | None = None
            self._pending_state: BrowserState | None = None
            self._initial_started: bool = False

        @override
        def compose(self) -> ComposeResult:
            address = (
                self._requested_location.value
                if isinstance(self._requested_location, Some)
                else ""
            )
            yield Input(
                value=address,
                placeholder="Markdown path, URL, gh owner/repository, or cb owner/repository",
                id="address",
                disabled=True,
            )
            with Horizontal(id="main"):
                with Vertical(id="sidebar", classes="-hidden"):
                    yield Label("Sidebar", id="sidebar-mode", markup=False)
                    yield ListView(id="sidebar-list", initial_index=None)
                yield BrowserMarkdownViewer(
                    """# Frogmouth

Browse Markdown without leaving the terminal.

Enter a local file, an HTTP(S) Markdown URL, `gh owner/repository`, or
`cb owner/repository` in the address field. Press **F1** for all shortcuts.
""",
                    show_table_of_contents=True,
                    open_links=False,
                    id="wviewer",
                )
            yield Footer()

        def on_mount(self) -> None:
            self._start_state_load()

        def _notify_error(self, message: str) -> None:
            self.notify(message, title="Frogmouth", severity="error")

        def _current_option(self) -> Option[Location]:
            if self._current_location is None:
                return Nothing()
            return Some(value=self._current_location)

        def _resolve(self, value: str) -> Location | None:
            result = resolve_location(
                value, self._current_option(), self._working_directory
            )
            if isinstance(result, Ok):
                return result.value
            else:
                self._notify_error(error_message(result.error))
                return None

        def _start_state_load(self) -> None:
            def read_persisted_state() -> StateLoaded:
                return StateLoaded(result=load_state(self._state_path))

            self._state_worker = self.run_worker(
                read_persisted_state,
                name="load-state",
                group="state-load",
                description=str(self._state_path),
                exit_on_error=False,
                thread=True,
            )

        def _start_initial_location(self) -> None:
            if self._initial_started:
                return
            self._initial_started = True
            self.query_one("#address", Input).disabled = False
            if isinstance(self._requested_location, Some):
                self._resolve_and_load(self._requested_location.value)

        def _start_document_load(
            self,
            location: Location,
            *,
            push: bool,
            history_index: int | None = None,
        ) -> None:
            def read_document() -> DocumentLoaded:
                return DocumentLoaded(
                    location=location,
                    push=push,
                    history_index=history_index,
                    result=load_document(location),
                )

            viewer = self.query_one("#wviewer", BrowserMarkdownViewer)
            viewer.loading = True
            self._document_worker = self.run_worker(
                read_document,
                name="load-document",
                group="documents",
                description=display_location(location),
                exit_on_error=False,
                exclusive=True,
                thread=True,
            )

        def _resolve_and_load(self, value: str) -> None:
            location = self._resolve(value)
            if location is not None:
                self._start_document_load(location, push=True)

        def _record_location(
            self,
            location: Location,
            *,
            push: bool,
            history_index: int | None,
        ) -> None:
            if history_index is not None:
                self._back_forward[history_index] = location
                self._back_forward_index = history_index
            elif push:
                del self._back_forward[self._back_forward_index + 1 :]
                self._back_forward.append(location)
                self._back_forward_index = len(self._back_forward) - 1
            elif self._back_forward_index < 0:
                self._back_forward.append(location)
                self._back_forward_index = 0
            else:
                self._back_forward[self._back_forward_index] = location
            self._current_location = location
            address = display_location(location)
            self.query_one("#address", Input).value = address
            self._apply_state(StateAction_AddHistory(location=address))

        def _apply_state(self, action: StateAction) -> None:
            self._browser_state = update_state(self._browser_state, action, 100)
            self._queue_state_save()
            _ = self.call_later(self._refresh_sidebar)

        def _queue_state_save(self) -> None:
            snapshot = self._browser_state
            if self._save_worker is not None:
                self._pending_state = snapshot
                return
            self._start_state_save(snapshot)

        def _start_state_save(self, snapshot: BrowserState) -> None:
            def write_persisted_state() -> StateSaved:
                return StateSaved(
                    state=snapshot, result=save_state(self._state_path, snapshot)
                )

            self._save_worker = self.run_worker(
                write_persisted_state,
                name="save-state",
                group="state-save",
                description=str(self._state_path),
                exit_on_error=False,
                thread=True,
            )

        def _finish_state_save(self) -> None:
            self._save_worker = None
            pending = self._pending_state
            self._pending_state = None
            if pending is not None:
                self._start_state_save(pending)

        async def _show_document(self, loaded: DocumentLoaded) -> None:
            result = loaded.result
            if isinstance(result, Err):
                self._notify_error(error_message(result.error))
            else:
                document = result.value
                viewer = self.query_one("#wviewer", BrowserMarkdownViewer)
                await viewer.document.update(document.markdown)
                if isinstance(document.location.fragment, Some):
                    if not viewer.document.goto_anchor(document.location.fragment.value):
                        self._notify_error(
                            f"Anchor not found: {document.location.fragment.value}"
                        )
                self.title = f"{document.title} — Frogmouth"
                self._record_location(
                    document.location,
                    push=loaded.push,
                    history_index=loaded.history_index,
                )

        async def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
            worker = cast(Worker[object], event.worker)
            document_worker: Worker[DocumentLoaded] | None = self._document_worker
            state_worker: Worker[StateLoaded] | None = self._state_worker
            save_worker: Worker[StateSaved] | None = self._save_worker
            if event.state in (WorkerState.PENDING, WorkerState.RUNNING):
                return
            if event.state == WorkerState.CANCELLED:
                if worker is document_worker:
                    self.query_one("#wviewer", BrowserMarkdownViewer).loading = False
                    self._document_worker = None
                elif worker is state_worker:
                    self._state_worker = None
                    self._start_initial_location()
                elif worker is save_worker:
                    self._finish_state_save()
                return
            if event.state == WorkerState.ERROR:
                detail = str(worker.error or "unknown background error")
                self._notify_error(f"Background operation failed: {detail}")
                if worker is document_worker:
                    self.query_one("#wviewer", BrowserMarkdownViewer).loading = False
                    self._document_worker = None
                elif worker is state_worker:
                    self._state_worker = None
                    self._start_initial_location()
                elif worker is save_worker:
                    self._finish_state_save()
                return
            if worker is document_worker and document_worker is not None:
                document_result: DocumentLoaded | None = document_worker.result
                if document_result is not None:
                    self.query_one("#wviewer", BrowserMarkdownViewer).loading = False
                    self._document_worker = None
                    await self._show_document(document_result)
                return
            if worker is state_worker and state_worker is not None:
                state_result: StateLoaded | None = state_worker.result
                if state_result is not None:
                    self._state_worker = None
                    if isinstance(state_result.result, Ok):
                        self._browser_state = state_result.result.value
                        await self._refresh_sidebar()
                    else:
                        self._notify_error(error_message(state_result.result.error))
                    self._start_initial_location()
                return
            if worker is save_worker and save_worker is not None:
                save_result: StateSaved | None = save_worker.result
                if save_result is not None:
                    if isinstance(save_result.result, Err):
                        self._notify_error(error_message(save_result.result.error))
                    self._finish_state_save()

        def on_input_submitted(self, event: Input.Submitted) -> None:
            _ = event.stop()
            self._resolve_and_load(event.value)

        def _is_markdown_link(self, location: Location) -> bool:
            if isinstance(location.kind, (LocationKind_GitHub, LocationKind_Codeberg)):
                return True
            if isinstance(location.kind, LocationKind_Local):
                suffix = Path(location.target).suffix.casefold()
                return not suffix or suffix in {".md", ".markdown"}
            else:
                path = PurePosixPath(urlsplit(location.target).path)
                return path.suffix.casefold() in {
                    ".md",
                    ".markdown",
                } or path.name.casefold() in {
                    "readme",
                    "changelog",
                }

        def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
            _ = event.stop()
            location = self._resolve(event.href)
            if location is None:
                return
            if (
                self._current_location is not None
                and location.kind == self._current_location.kind
                and location.target == self._current_location.target
                and isinstance(location.fragment, Some)
            ):
                viewer = self.query_one("#wviewer", BrowserMarkdownViewer)
                if viewer.document.goto_anchor(location.fragment.value):
                    self._record_location(location, push=True, history_index=None)
                else:
                    self._notify_error(f"Anchor not found: {location.fragment.value}")
                return
            if isinstance(location.kind, LocationKind_Remote) and not self._is_markdown_link(
                location
            ):
                self.open_url(display_location(location))
                return
            if isinstance(location.kind, LocationKind_Local) and not self._is_markdown_link(
                location
            ):
                self._notify_error(
                    f"Only Markdown documents open inside Frogmouth: {event.href}"
                )
                return
            self._start_document_load(location, push=True)

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            _ = event.stop()
            if isinstance(event.item, SidebarItem) and event.item.location is not None:
                self._resolve_and_load(event.item.location)

        async def _refresh_sidebar(self) -> None:
            mode = self._sidebar_mode
            if isinstance(mode, SidebarMode_Hidden):
                return
            mode_label = self.query_one("#sidebar-mode", Label)
            list_view = self.query_one("#sidebar-list", ListView)
            if isinstance(mode, SidebarMode_Help):
                mode_label.update("Help")
            elif isinstance(mode, SidebarMode_History):
                mode_label.update("History")
            else:
                mode_label.update("Bookmarks")
            await list_view.clear()
            items: list[SidebarItem]
            if isinstance(mode, SidebarMode_Help):
                items = [
                    SidebarItem("F1  Help sidebar"),
                    SidebarItem("h  History sidebar"),
                    SidebarItem("b  Bookmarks sidebar"),
                    SidebarItem("t  Toggle document contents"),
                    SidebarItem("Ctrl+B  Toggle bookmark"),
                    SidebarItem("Delete  Remove selected history"),
                    SidebarItem("Ctrl+Delete  Clear history"),
                    SidebarItem("d  Dock sidebar left/right"),
                    SidebarItem("Ctrl+R  Reload"),
                    SidebarItem(":  Focus address"),
                    SidebarItem("Alt+Left/Right  Back/forward"),
                    SidebarItem("j/s, k/w  Scroll by line"),
                    SidebarItem("Space  Scroll by page"),
                    SidebarItem("q  Quit"),
                ]
            elif isinstance(mode, SidebarMode_History):
                items = [SidebarItem(value, value) for value in self._browser_state.history]
                if not items:
                    items = [SidebarItem("Open a document to build history.", disabled=True)]
            else:
                items = [SidebarItem(value, value) for value in self._browser_state.bookmarks]
                if not items:
                    items = [SidebarItem("Press Ctrl+B on a document to bookmark it.", disabled=True)]
            await list_view.extend(items)
            list_view.index = 0 if items and not items[0].disabled else None

        async def _toggle_sidebar(self, requested: SidebarMode) -> None:
            sidebar = self.query_one("#sidebar", Vertical)
            self._sidebar_mode = toggle_sidebar(self._sidebar_mode, requested)
            if isinstance(self._sidebar_mode, SidebarMode_Hidden):
                _ = sidebar.add_class("-hidden")
                return
            _ = sidebar.remove_class("-hidden")
            await self._refresh_sidebar()
            _ = self.query_one("#sidebar-list", ListView).focus()

        async def action_help(self) -> None:
            await self._toggle_sidebar(SidebarMode_Help())

        async def action_history(self) -> None:
            await self._toggle_sidebar(SidebarMode_History())

        async def action_bookmarks(self) -> None:
            await self._toggle_sidebar(SidebarMode_Bookmarks())

        def action_toggle_toc(self) -> None:
            viewer = self.query_one("#wviewer", BrowserMarkdownViewer)
            viewer.show_table_of_contents = not viewer.show_table_of_contents

        def action_bookmark(self) -> None:
            if self._current_location is None:
                self._notify_error("Open a document before adding a bookmark.")
                return
            self._apply_state(
                StateAction_ToggleBookmark(
                    location=display_location(self._current_location)
                )
            )

        def action_delete_history(self) -> None:
            sidebar = self.query_one("#sidebar", Vertical)
            list_view = self.query_one("#sidebar-list", ListView)
            selected = list_view.highlighted_child
            if (
                sidebar.has_class("-hidden")
                or not isinstance(self._sidebar_mode, SidebarMode_History)
                or not isinstance(selected, SidebarItem)
                or selected.location is None
            ):
                self._notify_error("Select a history entry to delete.")
                return
            self._apply_state(StateAction_RemoveHistory(location=selected.location))

        def action_clear_history(self) -> None:
            self._apply_state(StateAction_ClearHistory())

        def action_dock_sidebar(self) -> None:
            sidebar = self.query_one("#sidebar", Vertical)
            self._sidebar_dock = toggle_sidebar_dock(self._sidebar_dock)
            dock_right = isinstance(self._sidebar_dock, SidebarDock_Right)
            sidebar.styles.dock = "right" if dock_right else "left"
            _ = sidebar.set_class(dock_right, "-right")

        def action_reload(self) -> None:
            if self._current_location is None:
                self._notify_error("Open a document before reloading.")
                return
            self._start_document_load(self._current_location, push=False)

        def action_focus_address(self) -> None:
            address = self.query_one("#address", Input)
            _ = address.focus()
            address.cursor_position = len(address.value)

        def action_history_back(self) -> None:
            target = self._back_forward_index - 1
            if target < 0:
                self._notify_error("There is no previous document.")
                return
            self._start_document_load(
                self._back_forward[target], push=False, history_index=target
            )

        def action_forward(self) -> None:
            target = self._back_forward_index + 1
            if target >= len(self._back_forward):
                self._notify_error("There is no next document.")
                return
            self._start_document_load(
                self._back_forward[target], push=False, history_index=target
            )

        def action_scroll_down(self) -> None:
            self.query_one("#wviewer", BrowserMarkdownViewer).scroll_down(animate=False)

        def action_scroll_up(self) -> None:
            self.query_one("#wviewer", BrowserMarkdownViewer).scroll_up(animate=False)

        def action_page_down(self) -> None:
            self.query_one("#wviewer", BrowserMarkdownViewer).scroll_page_down(
                animate=False
            )

    application: App[None] = FrogmouthApp(
        initial_location, working_directory, state_path
    )
    return application
