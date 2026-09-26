from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""The application's display name."""
APPLICATION_TITLE: Final[str] = "Frogmouth"

"""The command and package name."""
PACKAGE_NAME: Final[str] = "frogmouth"

"""The organisation name used for namespaced configuration and data directories."""
ORGANISATION_NAME: Final[str] = "textualize"

"""The upstream Frogmouth release whose behavior this program reproduces."""
VERSION: Final[str] = "0.9.1"

"""The User-Agent header value of every HTTP request."""
USER_AGENT: Final[str] = "frogmouth v0.9.1"

"""The Textualize Discord server opened by the discord command."""
DISCORD_URL: Final[str] = "https://discord.gg/Enf6Z3qhVr"

"""Address bar placeholder while no location is being viewed."""
ADDRESS_PLACEHOLDER: Final[str] = "Enter a location or command"

"""Markdown shown before any location has been viewed."""
PLACEHOLDER_MARKDOWN: Final[str] = "# Frogmouth 0.9.1\n\nWelcome to Frogmouth!\n"

"""The Markdown document of the help dialog (F1, the help command)."""
HELP_MARKDOWN: Final[str] = "# Frogmouth v0.9.1 Help\n\nWelcome to Frogmouth Help!\n\nFrogmouth was built with [Textual](https://github.com/Textualize/textual).\n\n\n## Navigation keys\n\n| Key | Command |\n| -- | -- |\n| `/` | Focus the address bar (`ctrl+u` to clear address bar) |\n| `Escape` | Return to address bar / clear address bar / quit |\n| `Ctrl+n` | Show/hide the navigation |\n| `Ctrl+b` | Show the bookmarks |\n| `Ctrl+l` | Show the local file browser |\n| `Ctrl+t` | Show the table of contents |\n| `Ctrl+y` | Show the history |\n| `Ctrl+left` | Go backward in history |\n| `Ctrl+right` | Go forward in history |\n\n## General keys\n\n| Key | Command |\n| -- | -- |\n| `Ctrl+d` | Add the current document to the bookmarks |\n| `Ctrl+r` | Reload the current document |\n| `Ctrl+q` | Quit the application |\n| `F1` | This help |\n| `F2` | Details about Frogmouth |\n| `F10` | Toggle dark/light theme |\n\n## Commands\n\nPress `/` or click the address bar, then enter any of the following commands:\n\n| Command | Aliases | Arguments | Command |\n| -- | -- | -- | -- |\n| `about` | `a` | | Show details about the application |\n| `bookmarks` | `b`, `bm` | | Show the bookmarks list |\n| `bitbucket` | `bb` | `<repo-info>` | View a file on BitBucket (see below) |\n| `codeberg` | `cb` | `<repo-info>` | View a file on Codeberg (see below) |\n| `changelog` | `cl` | | View the Frogmouth ChangeLog |\n| `chdir` | `cd` | `<dir>` | Switch the local file browser to a new directory |\n| `contents` | `c`, `toc` | | Show the table of contents for the document |\n| `discord` | | | Visit the Textualize Discord server |\n| `github` | `gh` | `<repo-info>` | View a file on GitHub (see below) |\n| `gitlab` | `gl` | `<repo-info>` | View a file on GitLab (see below) |\n| `help` | `?` | | Show this document |\n| `history` | `h` | | Show the history |\n| `local` | `l` | | Show the local file browser |\n| `quit` | `q` | | Quit the viewer |\n\n## Git forge quick view\n\nThe git forge quick view command can be used to quickly view a file on a git\nforge such as GitHub or GitLab. Various forms of specifying the repository,\nbranch and file are supported. For example:\n\n- `<owner>`/`<repo>`\n- `<owner>`/`<repo>` `<file>`\n- `<owner>` `<repo>`\n- `<owner>` `<repo>` `<file>`\n- `<owner>`/`<repo>`:`<branch>`\n- `<owner>`/`<repo>`:`<branch>` `<file>`\n- `<owner>` `<repo>`:`<branch>`\n- `<owner>` `<repo>`:`<branch>` `<file>`\n\nAnywhere where `<file>` is omitted it is assumed `README.md` is desired.\n\nAnywhere where `<branch>` is omitted a test is made for the desired file on\nfirst a `main` and then a `master` branch.\n"

"""Rich markup title of the about dialog (F2, the about command)."""
ABOUT_TITLE: Final[str] = "Frogmouth [b dim]v0.9.1"

"""Rich markup body of the about dialog. Each @click action asks the application
to open the quoted URL externally."""
ABOUT_MESSAGE: Final[str] = "Built with [@click=app.visit('https://textual.textualize.io/')]Textual[/] by [@click=app.visit('https://www.textualize.io/')]Textualize[/].\n\n[@click=app.visit('https://github.com/textualize/frogmouth')]https://github.com/textualize/frogmouth[/]"

"""Prompt of the bookmark title input dialog."""
BOOKMARK_TITLE_PROMPT: Final[str] = "Bookmark title:"

DELETE_BOOKMARK_TITLE: Final[str] = "Delete bookmark"

DELETE_BOOKMARK_QUESTION: Final[str] = "Are you sure you want to delete the bookmark?"

DELETE_HISTORY_TITLE: Final[str] = "Delete history entry?"

DELETE_HISTORY_QUESTION: Final[str] = "Are you sure you want to delete the history entry?"

CLEAR_HISTORY_TITLE: Final[str] = "Clear history?"

CLEAR_HISTORY_QUESTION: Final[str] = "Are you sure you want to clear everything out of history?"

__all__ = ["ABOUT_MESSAGE", "ABOUT_TITLE", "ADDRESS_PLACEHOLDER", "APPLICATION_TITLE", "BOOKMARK_TITLE_PROMPT", "CLEAR_HISTORY_QUESTION", "CLEAR_HISTORY_TITLE", "DELETE_BOOKMARK_QUESTION", "DELETE_BOOKMARK_TITLE", "DELETE_HISTORY_QUESTION", "DELETE_HISTORY_TITLE", "DISCORD_URL", "HELP_MARKDOWN", "ORGANISATION_NAME", "PACKAGE_NAME", "PLACEHOLDER_MARKDOWN", "USER_AGENT", "VERSION"]
