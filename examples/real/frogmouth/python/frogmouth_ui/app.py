"""Textual screen shell of the Frogmouth reimplementation.

Every decision (address interpretation, loading, link handling, history,
bookmarks, configuration, sidebar and Escape behaviour, texts) is made by the
generated Cott facades imported below. This module only builds widgets,
forwards user events to those facades and applies the values they return.
"""

import os
import sys
from collections.abc import Iterable
from functools import partial
from pathlib import Path
from typing import ClassVar

import textual
from cott_runtime import CottList, Err, Nothing, Option, Some
from frogmouth.bookmarks import (
    Bookmark,
    add_bookmark,
    bookmark_entries,
    delete_bookmark,
    rename_bookmark,
    suggest_bookmark_title,
)
from frogmouth.branding import (
    ABOUT_MESSAGE,
    ABOUT_TITLE,
    ADDRESS_PLACEHOLDER,
    APPLICATION_TITLE,
    BOOKMARK_TITLE_PROMPT,
    CLEAR_HISTORY_QUESTION,
    CLEAR_HISTORY_TITLE,
    DELETE_BOOKMARK_QUESTION,
    DELETE_BOOKMARK_TITLE,
    DELETE_HISTORY_QUESTION,
    DELETE_HISTORY_TITLE,
    PLACEHOLDER_MARKDOWN,
)
from frogmouth.browser import (
    BrowserState,
    NavigationEffect_ChangeDirectory,
    NavigationEffect_Display,
    NavigationEffect_Failed,
    NavigationEffect_OpenExternally,
    NavigationEffect_Quit,
    NavigationEffect_ScrollToAnchor,
    NavigationEffect_ShowAbout,
    NavigationEffect_ShowHelp,
    NavigationEffect_ShowPane,
    NavigationRequest,
    NavigationRequest_Address,
    NavigationRequest_Back,
    NavigationRequest_Forward,
    NavigationRequest_HistoryEntry,
    NavigationRequest_Link,
    NavigationRequest_Open,
    NavigationRequest_Paste,
    NavigationRequest_Reload,
    NavigationRequest_Startup,
    NavigationResult,
    ViewState_Placeholder,
    navigate,
    viewed_location,
)
from frogmouth.cli import (
    CommandLine_Browse,
    CommandLine_Invalid,
    CommandLine_ShowHelp,
    CommandLine_ShowVersion,
    parse_command_line,
)
from frogmouth.config import (
    AppDirectories,
    Config,
    Dock_Left,
    Theme_Light,
    application_directories,
    default_config,
    toggle_dock,
    toggle_theme,
)
from frogmouth.document import (
    BrowserFailure,
    BrowserFailure_NotBookmarkable,
    failure_dialog,
    open_external,
    select_browsable_entries,
)
from frogmouth.history import History, delete_history_entry, history_entries, start_history
from frogmouth.layout import (
    CycleDirection_Next,
    CycleDirection_Previous,
    EscapeAction_ClearAddress,
    EscapeAction_FocusAddress,
    EscapeAction_HideSidebarAndFocusAddress,
    EscapeAction_Quit,
    Focus_AddressBar,
    Focus_Document,
    Focus_Sidebar,
    Pane,
    Pane_Bookmarks,
    Pane_Contents,
    Pane_History,
    Pane_Local,
    Sidebar,
    Visibility_Hidden,
    Visibility_Shown,
    cycle_pane,
    escape_action,
    toggle_pane,
    toggle_sidebar,
)
from frogmouth.model import BrowserContext, Dialog, Location, LocationKind_Local
from frogmouth.storage import (
    StoreError,
    load_bookmarks,
    load_config,
    load_history,
    save_bookmarks,
    save_config,
    save_history,
    storage_failure_dialog,
)
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Input, Markdown, OptionList, TabbedContent, TabPane, Tree
from textual.widgets.markdown import MarkdownTableOfContents
from textual.widgets.option_list import Option as ListOption
from textual.worker import Worker, WorkerState

from frogmouth_ui.dialogs import ErrorDialog, HelpDialog, InformationDialog, InputDialog, YesNoDialog

_PANE_IDS: dict[type[object], str] = {
    Pane_Contents: "contents",
    Pane_Local: "local",
    Pane_Bookmarks: "bookmarks",
    Pane_History: "history",
}
_PANES: dict[str, Pane] = {
    "contents": Pane_Contents(),
    "local": Pane_Local(),
    "bookmarks": Pane_Bookmarks(),
    "history": Pane_History(),
}


class Viewer(VerticalScroll, can_focus=True, can_focus_children=True):
    """The scrolling document area."""

    DEFAULT_CSS = """
    Viewer {
        width: 1fr;
        scrollbar-gutter: stable;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("w,k", "scroll_up", "", show=False),
        Binding("s,j", "scroll_down", "", show=False),
        Binding("space", "page_down", "", show=False),
        Binding("b", "page_up", "", show=False),
    ]


class LocalTree(DirectoryTree):
    """The local file browser; the generated facade decides which entries are listed."""

    def __init__(self, path: str, extensions: CottList[str]) -> None:
        super().__init__(path)
        self._extensions = extensions

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        listing = list(paths)
        kept = set(select_browsable_entries(CottList(values=[str(path) for path in listing]), self._extensions))
        return [path for path in listing if str(path) in kept]


class BookmarksPane(TabPane):
    """The bookmarks pane."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("delete", "delete", "Delete the bookmark"),
        Binding("r", "rename", "Rename the bookmark"),
    ]

    def action_delete(self) -> None:
        highlighted = self.query_one(OptionList).highlighted
        if highlighted is not None and isinstance(self.screen, MainScreen):
            self.screen.confirm_delete_bookmark(highlighted)

    def action_rename(self) -> None:
        highlighted = self.query_one(OptionList).highlighted
        if highlighted is not None and isinstance(self.screen, MainScreen):
            self.screen.ask_rename_bookmark(highlighted)


class HistoryPane(TabPane):
    """The history pane."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("delete", "delete", "Delete the history item"),
        Binding("backspace", "clear", "Clean the history"),
    ]

    def action_delete(self) -> None:
        options = self.query_one(OptionList)
        highlighted = options.highlighted
        if highlighted is not None and isinstance(self.screen, MainScreen):
            option_id = options.get_option_at_index(highlighted).id
            if option_id is not None:
                self.screen.confirm_delete_history(int(option_id))

    def action_clear(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.confirm_clear_history()


class Navigation(Vertical, can_focus=False, can_focus_children=True):
    """The navigation sidebar."""

    DEFAULT_CSS = """
    Navigation {
        width: 44;
        background: $panel;
        dock: left;
    }

    Navigation TabbedContent {
        height: 100%;
    }

    Navigation ContentSwitcher {
        height: 1fr;
    }

    Navigation OptionList, Navigation DirectoryTree, Navigation MarkdownTableOfContents {
        background: $panel;
        border: none;
        height: 1fr;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("comma,a,ctrl+left,shift+left,h", "previous_tab", "", show=False),
        Binding("full_stop,d,ctrl+right,shift+right,l", "next_tab", "", show=False),
        Binding("backslash", "toggle_dock", "Dock left/right"),
    ]

    def action_previous_tab(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.cycle_sidebar(forward=False)

    def action_next_tab(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.cycle_sidebar(forward=True)

    def action_toggle_dock(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.toggle_dock()


class MainScreen(Screen[None]):
    """The browser screen."""

    DEFAULT_CSS = """
    .focusable {
        border: blank;
    }

    .focusable:focus {
        border: heavy $accent !important;
    }

    #omnibox {
        dock: top;
        padding: 0;
        height: 3;
    }

    #omnibox .input--placeholder {
        color: $text 50%;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("slash,colon", "omnibox", "Omnibox", show=False),
        Binding("ctrl+b", "pane('bookmarks')", "", show=False),
        Binding("ctrl+d", "bookmark_this", "", show=False),
        Binding("ctrl+l", "pane('local')", "", show=False),
        Binding("ctrl+left", "backward", "", show=False),
        Binding("ctrl+right", "forward", "", show=False),
        Binding("ctrl+r", "reload", "", show=False),
        Binding("ctrl+t", "pane('contents')", "", show=False),
        Binding("ctrl+y", "pane('history')", "", show=False),
        Binding("escape", "escape", "", show=False),
        Binding("f1", "help", "Help"),
        Binding("f2", "about", "About"),
        Binding("ctrl+n", "navigation", "Navigation"),
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("f10", "toggle_theme", "", show=False),
    ]

    def __init__(
        self,
        startup: Option[str],
        context: BrowserContext,
        directories: AppDirectories,
        config: Config,
        history: History,
        bookmarks: CottList[Bookmark],
        problems: list[Dialog],
    ) -> None:
        super().__init__()
        self._startup = startup
        self._browser_context = context
        self._directories = directories
        self._config = config
        self._session = BrowserState(history=history, view=ViewState_Placeholder())
        self._bookmarks = bookmarks
        self._problems = problems
        self._sidebar = Sidebar(visibility=Visibility_Hidden(), active=Pane_Contents())
        self._markdown = Markdown(PLACEHOLDER_MARKDOWN, open_links=False)

    def compose(self) -> ComposeResult:
        yield Input(placeholder=ADDRESS_PLACEHOLDER, id="omnibox", classes="focusable")
        with Horizontal():
            with Navigation():
                with TabbedContent(initial="contents"):
                    with TabPane("Contents", id="contents"):
                        yield MarkdownTableOfContents(self._markdown)
                    with TabPane("Local", id="local"):
                        yield LocalTree(self._browser_context.home, self._browser_context.markdown_extensions)
                    with BookmarksPane("Bookmarks", id="bookmarks"):
                        yield OptionList()
                    with HistoryPane("History", id="history"):
                        yield OptionList()
            with Viewer(classes="focusable"):
                yield self._markdown
        yield Footer()

    def on_mount(self) -> None:
        self._markdown.can_focus_children = False
        self._apply_sidebar(focus=False)
        self._apply_dock()
        self._refresh_bookmarks()
        self._refresh_history()
        for problem in self._problems:
            self.app.push_screen(ErrorDialog(problem))
        self._navigate(NavigationRequest_Startup(address=self._startup))

    # Navigation through the generated root.

    def _navigate(self, request: NavigationRequest) -> None:
        self.run_worker(
            partial(navigate, self._session, request, self._browser_context),
            name="navigate",
            group="navigate",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    async def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group != "navigate":
            return
        if event.state == WorkerState.SUCCESS and isinstance(event.worker.result, NavigationResult):
            await self._apply(event.worker.result)
        elif event.state == WorkerState.ERROR:
            self.app.push_screen(ErrorDialog(Dialog(title="Navigation failed", message=Text(str(event.worker.error)).markup)))

    async def _apply(self, result: NavigationResult) -> None:
        previous = self._session
        self._session = result.session
        if result.session.history != previous.history:
            self._history_changed()
        address = self.query_one("#omnibox", Input)
        if isinstance(result.address, Some):
            address.value = result.address.value
        viewed = viewed_location(self._session)
        address.placeholder = viewed.value.target if isinstance(viewed, Some) else ADDRESS_PLACEHOLDER
        effect = result.effect
        if isinstance(effect, NavigationEffect_Display):
            await self._markdown.update(effect.document.markdown)
            viewer = self.query_one(Viewer)
            viewer.scroll_home(animate=False)
            if isinstance(effect.anchor, Some):
                self._markdown.goto_anchor(effect.anchor.value)
            viewer.focus()
        elif isinstance(effect, NavigationEffect_ScrollToAnchor):
            self._markdown.goto_anchor(effect.anchor)
        elif isinstance(effect, NavigationEffect_OpenExternally):
            open_external(effect.target)
        elif isinstance(effect, NavigationEffect_ChangeDirectory):
            self.query_one(LocalTree).path = Path(effect.path)
            self._sidebar = Sidebar(visibility=Visibility_Shown(), active=Pane_Local())
            self._apply_sidebar(focus=True)
        elif isinstance(effect, NavigationEffect_ShowPane):
            self._sidebar = toggle_pane(self._sidebar, effect.pane)
            self._apply_sidebar(focus=True)
        elif isinstance(effect, NavigationEffect_ShowHelp):
            self.action_help()
        elif isinstance(effect, NavigationEffect_ShowAbout):
            self.action_about()
        elif isinstance(effect, NavigationEffect_Quit):
            self.app.exit()
        elif isinstance(effect, NavigationEffect_Failed):
            self._show_failure(effect.failure)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "omnibox":
            event.stop()
            self._navigate(NavigationRequest_Address(value=event.value))

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        event.stop()
        self._navigate(NavigationRequest_Link(href=event.href))

    def on_paste(self, event: events.Paste) -> None:
        self._navigate(NavigationRequest_Paste(text=event.text))

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self._navigate(NavigationRequest_Open(location=Location(kind=LocationKind_Local(), target=str(event.path))))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        pane = event.option_list.parent
        if isinstance(pane, BookmarksPane):
            self._navigate(NavigationRequest_Open(location=self._bookmarks[event.option_index].location))
        elif isinstance(pane, HistoryPane) and event.option.id is not None:
            self._navigate(NavigationRequest_HistoryEntry(history_id=int(event.option.id)))

    def on_markdown_table_of_contents_updated(self, event: Markdown.TableOfContentsUpdated) -> None:
        if event.markdown is self._markdown:
            self.query_one(MarkdownTableOfContents).table_of_contents = event.table_of_contents

    def on_markdown_table_of_contents_selected(self, event: Markdown.TableOfContentsSelected) -> None:
        event.stop()
        self.query_one(Viewer).scroll_to_widget(self._markdown.query_one(f"#{event.block_id}"), top=True)

    def action_backward(self) -> None:
        self._navigate(NavigationRequest_Back())

    def action_forward(self) -> None:
        self._navigate(NavigationRequest_Forward())

    def action_reload(self) -> None:
        self._navigate(NavigationRequest_Reload())

    # Sidebar, focus and Escape.

    def action_omnibox(self) -> None:
        self.query_one("#omnibox", Input).focus()

    def action_pane(self, pane_id: str) -> None:
        self._sidebar = toggle_pane(self._sidebar, _PANES[pane_id])
        self._apply_sidebar(focus=True)

    def action_navigation(self) -> None:
        self._sidebar = toggle_sidebar(self._sidebar)
        self._apply_sidebar(focus=False)

    def cycle_sidebar(self, forward: bool) -> None:
        direction = CycleDirection_Next() if forward else CycleDirection_Previous()
        self._sidebar = cycle_pane(self._sidebar, direction)
        self._apply_sidebar(focus=True)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        pane_id = event.pane.id
        if pane_id in _PANES:
            self._sidebar = Sidebar(visibility=self._sidebar.visibility, active=_PANES[pane_id])

    def _apply_sidebar(self, focus: bool) -> None:
        navigation = self.query_one(Navigation)
        shown = isinstance(self._sidebar.visibility, Visibility_Shown)
        navigation.display = shown
        pane_id = _PANE_IDS[type(self._sidebar.active)]
        self.query_one(TabbedContent).active = pane_id
        if not shown:
            self.query_one(Viewer).focus()
        elif focus:
            pane = self.query_one(f"#{pane_id}", TabPane)
            target = pane.query(Tree).first() if pane_id == "contents" else pane.query_one("OptionList, DirectoryTree")
            target.focus(scroll_visible=False)

    def action_escape(self) -> None:
        address = self.query_one("#omnibox", Input)
        if address.has_focus:
            focus = Focus_AddressBar()
        elif self.query_one(Navigation).has_focus_within:
            focus = Focus_Sidebar()
        else:
            focus = Focus_Document()
        action = escape_action(focus, address.value)
        if isinstance(action, EscapeAction_ClearAddress):
            address.value = ""
        elif isinstance(action, EscapeAction_Quit):
            self.app.exit()
        elif isinstance(action, EscapeAction_HideSidebarAndFocusAddress):
            if isinstance(self._sidebar.visibility, Visibility_Shown):
                self._sidebar = toggle_sidebar(self._sidebar)
                self._apply_sidebar(focus=False)
            address.focus()
        elif isinstance(action, EscapeAction_FocusAddress):
            address.focus()

    # Dialogs.

    def action_help(self) -> None:
        self.app.push_screen(HelpDialog())

    def action_about(self) -> None:
        self.app.push_screen(InformationDialog(Dialog(title=ABOUT_TITLE, message=ABOUT_MESSAGE)))

    def _show_failure(self, failure: BrowserFailure) -> None:
        self.app.push_screen(ErrorDialog(failure_dialog(failure)))

    def _report_store_error(self, error: StoreError) -> None:
        self.app.push_screen(ErrorDialog(storage_failure_dialog(error)))

    # History.

    def _history_changed(self) -> None:
        saved = save_history(self._directories.data_directory, self._session.history.locations)
        if isinstance(saved, Err):
            self._report_store_error(saved.error)
        self._refresh_history()

    def _refresh_history(self) -> None:
        options = self.query_one("#history OptionList", OptionList)
        options.clear_options()
        options.add_options(
            [
                ListOption(Text.from_markup(entry.prompt, overflow="ellipsis"), id=str(entry.history_id))
                for entry in history_entries(self._session.history)
            ]
        )

    def confirm_delete_history(self, history_id: int) -> None:
        self.app.push_screen(
            YesNoDialog(DELETE_HISTORY_TITLE, DELETE_HISTORY_QUESTION),
            partial(self._delete_history, history_id),
        )

    def _delete_history(self, history_id: int, confirmed: bool | None) -> None:
        if not confirmed:
            return
        remaining = delete_history_entry(self._session.history, history_id)
        if isinstance(remaining, Some):
            self._session = BrowserState(history=remaining.value, view=self._session.view)
            self._history_changed()

    def confirm_clear_history(self) -> None:
        self.app.push_screen(YesNoDialog(CLEAR_HISTORY_TITLE, CLEAR_HISTORY_QUESTION), self._clear_history)

    def _clear_history(self, confirmed: bool | None) -> None:
        if confirmed:
            self._session = BrowserState(history=start_history(CottList(values=())), view=self._session.view)
            self._history_changed()

    # Bookmarks.

    def _refresh_bookmarks(self) -> None:
        options = self.query_one("#bookmarks OptionList", OptionList)
        highlighted = options.highlighted
        options.clear_options()
        options.add_options([ListOption(Text.from_markup(prompt, overflow="ellipsis")) for prompt in bookmark_entries(self._bookmarks)])
        if highlighted is not None and len(self._bookmarks) > 0:
            options.highlighted = min(highlighted, len(self._bookmarks) - 1)

    def _store_bookmarks(self, bookmarks: CottList[Bookmark]) -> None:
        self._bookmarks = bookmarks
        saved = save_bookmarks(self._directories.data_directory, bookmarks)
        if isinstance(saved, Err):
            self._report_store_error(saved.error)
        self._refresh_bookmarks()

    def action_bookmark_this(self) -> None:
        viewed = viewed_location(self._session)
        if not isinstance(viewed, Some):
            self._show_failure(BrowserFailure_NotBookmarkable())
            return
        location = viewed.value
        self.app.push_screen(
            InputDialog(BOOKMARK_TITLE_PROMPT, suggest_bookmark_title(location)),
            partial(self._add_bookmark, location),
        )

    def _add_bookmark(self, location: Location, title: str | None) -> None:
        if title is not None:
            self._store_bookmarks(add_bookmark(self._bookmarks, title, location))

    def confirm_delete_bookmark(self, index: int) -> None:
        self.app.push_screen(
            YesNoDialog(DELETE_BOOKMARK_TITLE, DELETE_BOOKMARK_QUESTION),
            partial(self._delete_bookmark, index),
        )

    def _delete_bookmark(self, index: int, confirmed: bool | None) -> None:
        if confirmed and index < len(self._bookmarks):
            self._store_bookmarks(delete_bookmark(self._bookmarks, index))

    def ask_rename_bookmark(self, index: int) -> None:
        self.app.push_screen(
            InputDialog(BOOKMARK_TITLE_PROMPT, self._bookmarks[index].title),
            partial(self._rename_bookmark, index),
        )

    def _rename_bookmark(self, index: int, title: str | None) -> None:
        if title is not None and index < len(self._bookmarks):
            self._store_bookmarks(rename_bookmark(self._bookmarks, index, title))

    # Configuration.

    def action_toggle_theme(self) -> None:
        self._store_config(toggle_theme(self._config))
        self.app.theme = _theme_name(self._config)

    def toggle_dock(self) -> None:
        self._store_config(toggle_dock(self._config))
        self._apply_dock()

    def _store_config(self, config: Config) -> None:
        self._config = config
        saved = save_config(self._directories.config_directory, config)
        if isinstance(saved, Err):
            self._report_store_error(saved.error)

    def _apply_dock(self) -> None:
        self.query_one(Navigation).styles.dock = "left" if isinstance(self._config.navigation_dock, Dock_Left) else "right"


def _theme_name(config: Config) -> str:
    return "textual-light" if isinstance(config.theme, Theme_Light) else "textual-dark"


class FrogmouthApp(App[None]):
    """The Frogmouth application."""

    TITLE = APPLICATION_TITLE

    def __init__(
        self,
        startup: Option[str],
        context: BrowserContext,
        directories: AppDirectories,
        config: Config,
        history: History,
        bookmarks: CottList[Bookmark],
        problems: list[Dialog],
    ) -> None:
        super().__init__()
        self._startup = startup
        self._browser_context = context
        self._directories = directories
        self._config = config
        self._history = history
        self._bookmarks = bookmarks
        self._problems = problems

    def on_mount(self) -> None:
        self.theme = _theme_name(self._config)
        self.push_screen(MainScreen(self._startup, self._browser_context, self._directories, self._config, self._history, self._bookmarks, self._problems))

    def action_visit(self, url: str) -> None:
        open_external(url)


def _environment(name: str) -> Option[str]:
    value = os.environ.get(name)
    return Some(value=value) if value is not None else Nothing()


def run() -> int:
    """Run the command line: print help, version or usage errors, or start the browser."""
    command = parse_command_line(CottList(values=sys.argv[1:]), textual.__version__)
    if isinstance(command, CommandLine_ShowHelp | CommandLine_ShowVersion):
        print(command.text)
        return 0
    if isinstance(command, CommandLine_Invalid):
        print(command.message, file=sys.stderr)
        return 2
    assert isinstance(command, CommandLine_Browse)
    home = str(Path.home())
    directories = application_directories(home, _environment("XDG_CONFIG_HOME"), _environment("XDG_DATA_HOME"))
    problems: list[Dialog] = []
    loaded_config = load_config(directories.config_directory)
    if isinstance(loaded_config, Err):
        problems.append(storage_failure_dialog(loaded_config.error))
        config = default_config()
    else:
        config = loaded_config.value.config
    loaded_history = load_history(directories.data_directory)
    if isinstance(loaded_history, Err):
        problems.append(storage_failure_dialog(loaded_history.error))
        history = start_history(CottList(values=()))
    else:
        history = loaded_history.value
    loaded_bookmarks = load_bookmarks(directories.data_directory)
    if isinstance(loaded_bookmarks, Err):
        problems.append(storage_failure_dialog(loaded_bookmarks.error))
        bookmarks: CottList[Bookmark] = CottList(values=())
    else:
        bookmarks = loaded_bookmarks.value.bookmarks
    context = BrowserContext(home=home, working_directory=os.getcwd(), markdown_extensions=config.markdown_extensions)
    app = FrogmouthApp(command.address, context, directories, config, history, bookmarks, problems)
    app.run()
    return app.return_code or 0
