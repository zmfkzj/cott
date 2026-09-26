"""Modal dialogs of the Frogmouth screen shell; their text comes from generated facades."""

from typing import ClassVar

from cott_runtime import Some
from frogmouth.bookmarks import accept_dialog_text
from frogmouth.branding import HELP_MARKDOWN
from frogmouth.document import open_external
from frogmouth.model import Dialog
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Markdown, Static


class TextDialog(ModalScreen[None]):
    """A dialog showing a Rich-markup title and message with an OK button."""

    DEFAULT_CSS = """
    TextDialog {
        align: center middle;
    }

    TextDialog Center {
        width: 100%;
    }

    TextDialog > Vertical {
        background: $boost;
        min-width: 30%;
        width: auto;
        height: auto;
        border: round $primary;
    }

    TextDialog Static {
        width: auto;
    }

    TextDialog .spaced {
        padding: 1 4;
    }

    TextDialog #message {
        min-width: 100%;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "dismiss(None)", "", show=False)]

    def __init__(self, dialog: Dialog) -> None:
        super().__init__()
        self._dialog = dialog

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield Static(self._dialog.title, classes="spaced")
            yield Static(self._dialog.message, id="message", classes="spaced")
            with Center(classes="spaced"):
                yield Button("OK", variant=self.button_variant())

    def button_variant(self) -> str:
        return "primary"

    def on_mount(self) -> None:
        self.query_one(Button).focus()

    def on_button_pressed(self) -> None:
        self.dismiss(None)


class ErrorDialog(TextDialog):
    """A dialog reporting a failure."""

    DEFAULT_CSS = """
    ErrorDialog > Vertical {
        background: $error 15%;
        border: thick $error 50%;
    }

    ErrorDialog #message {
        border-top: solid $panel;
        border-bottom: solid $panel;
    }
    """

    def button_variant(self) -> str:
        return "error"


class InformationDialog(TextDialog):
    """A dialog showing information such as the about text."""

    DEFAULT_CSS = """
    InformationDialog > Vertical {
        border: thick $primary 50%;
    }
    """


class InputDialog(ModalScreen[str]):
    """A dialog asking for one line of text; blank answers keep it open."""

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }

    InputDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    InputDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    InputDialog Input {
        width: 40;
        margin: 1;
    }

    InputDialog Label {
        margin-left: 2;
    }

    InputDialog Button {
        margin-right: 1;
    }

    InputDialog #buttons {
        width: 100%;
        align-horizontal: right;
        padding-right: 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "app.pop_screen", "", show=False)]

    def __init__(self, prompt: str, initial: str) -> None:
        super().__init__()
        self._prompt = prompt
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical():
            with Vertical(id="input"):
                yield Label(self._prompt)
                yield Input(self._initial)
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    @on(Button.Pressed, "#cancel")
    def cancel_input(self) -> None:
        self.app.pop_screen()

    @on(Input.Submitted)
    @on(Button.Pressed, "#ok")
    def accept_input(self) -> None:
        accepted = accept_dialog_text(self.query_one(Input).value)
        if isinstance(accepted, Some):
            self.dismiss(accepted.value)


class YesNoDialog(ModalScreen[bool]):
    """A dialog asking a yes/no question."""

    DEFAULT_CSS = """
    YesNoDialog {
        align: center middle;
    }

    YesNoDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    YesNoDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    YesNoDialog Static {
        width: auto;
    }

    YesNoDialog .spaced {
        padding: 1;
    }

    YesNoDialog #question {
        min-width: 100%;
        border-top: solid $primary;
        border-bottom: solid $primary;
    }

    YesNoDialog Button {
        margin-right: 1;
    }

    YesNoDialog #buttons {
        width: 100%;
        align-horizontal: right;
        padding-right: 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("left,up", "focus_previous", "", show=False),
        Binding("right,down", "focus_next", "", show=False),
        Binding("escape", "app.pop_screen", "", show=False),
    ]

    def __init__(self, title: str, question: str) -> None:
        super().__init__()
        self._title = title
        self._question = question

    def compose(self) -> ComposeResult:
        with Vertical():
            with Center():
                yield Static(self._title, classes="spaced")
            yield Static(self._question, id="question", classes="spaced")
            with Horizontal(id="buttons"):
                yield Button("Yes", id="yes", variant="primary")
                yield Button("No", id="no")

    def on_mount(self) -> None:
        self.query(Button).first().focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class HelpDialog(ModalScreen[None]):
    """The help document (F1)."""

    DEFAULT_CSS = """
    HelpDialog {
        align: center middle;
    }

    HelpDialog > Vertical {
        border: thick $primary 50%;
        width: 80%;
        height: 80%;
        background: $boost;
    }

    HelpDialog > Vertical > VerticalScroll {
        height: 1fr;
        margin: 1 2;
    }

    HelpDialog > Vertical > Center {
        padding: 1;
        height: auto;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape,f1", "dismiss(None)", "", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical():
            with VerticalScroll():
                yield Markdown(HELP_MARKDOWN, open_links=False)
            with Center():
                yield Button("Close", variant="primary")

    def on_mount(self) -> None:
        self.query_one(Markdown).can_focus_children = False
        self.query_one("Vertical > VerticalScroll").focus()

    def on_button_pressed(self) -> None:
        self.dismiss(None)

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        event.stop()
        open_external(event.href)
