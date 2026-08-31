from pathlib import Path
from typing import ClassVar, final

from cott_runtime import Err, Option, Some
from frogmouth.document import load_document
from frogmouth.model import Document
from frogmouth.navigation import display_location, resolve_location
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Input, MarkdownViewer


def create_browser_app(initial_location: Option[str], working_directory: Path) -> App[None]:
    @final
    class FrogmouthApp(App[None]):
        CSS: ClassVar[str] = "#viewer { height: 1fr; }"
        BINDINGS: ClassVar[list[BindingType]] = [
            Binding("ctrl+l", "address", "Address"),
            Binding("ctrl+r", "reload", "Reload"),
            Binding("q", "quit", "Quit"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self._initial = initial_location
            self._cwd = working_directory
            self._document: Document | None = None

        def compose(self) -> ComposeResult:
            address = self._initial.value if isinstance(self._initial, Some) else ""
            yield Input(address, placeholder="Markdown path or HTTP(S) URL", id="address")
            yield MarkdownViewer("# Frogmouth\n\nOpen a Markdown document.", id="viewer")
            yield Footer()

        def on_mount(self) -> None:
            if isinstance(self._initial, Some):
                self._open(self._initial.value)

        def on_input_submitted(self, event: Input.Submitted) -> None:
            event.stop()
            self._open(event.value)

        def _open(self, value: str) -> None:
            resolved = resolve_location(value, self._cwd)
            if isinstance(resolved, Err):
                self.notify(str(resolved.error), severity="error")
                return
            loaded = load_document(resolved.value)
            if isinstance(loaded, Err):
                self.notify(str(loaded.error), severity="error")
                return
            self._document = loaded.value
            self.title = f"{loaded.value.title} — Frogmouth"
            self.query_one("#address", Input).value = display_location(loaded.value.location)
            self.call_later(self._render)

        async def _render(self) -> None:
            if self._document is not None:
                await self.query_one("#viewer", MarkdownViewer).document.update(
                    self._document.markdown
                )

        def action_address(self) -> None:
            self.query_one("#address", Input).focus()

        def action_reload(self) -> None:
            if self._document is not None:
                self._open(display_location(self._document.location))

    return FrogmouthApp()
