# https://github.com/Textualize/frogmouth

Cott reimplementation of Frogmouth, the terminal Markdown browser, aiming at feature parity with
upstream release [`v0.9.1`](https://github.com/Textualize/frogmouth/releases/tag/v0.9.1) (commit
`e7b45da528e8eddd0c6e107df4e601e62c0c3709`). Cott contracts own the browser's behaviour: command
line, address bar and commands, location resolution, local and web loading, link following,
forge quick views, history, bookmarks, configuration, sidebar and Escape logic, and
the main user-visible copy. Rendering and the table-of-contents tree are supplied by
Textual's `Markdown`/`MarkdownTableOfContents` widgets, as in upstream. See
Deviations for deliberate behaviour changes.

## Run

```bash
project=examples/real/frogmouth
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" -m frogmouth_ui README.md
```

`frogmouth_ui` accepts the upstream command line (`[-h] [-v] [file ...]`; `frogmouth gh
textualize/textual` style shortcuts are joined into one address). Configuration lives in
`$XDG_CONFIG_HOME/textualize/frogmouth/configuration.json` and history and bookmarks in
`$XDG_DATA_HOME/textualize/frogmouth/{history,bookmarks}.json`, with the XDG defaults
`~/.config` and `~/.local/share`, in upstream's JSON formats.

## Architecture

Generated Python implementations may not define classes, and Textual widgets and screens are
classes, so the program is split in two:

- `src/real/frogmouth/*.cott` (13 modules, 48 callables, all agent-generated). The root is
  `frogmouth.browser.navigate`: one navigation request (startup, address-bar text, link, paste,
  local-file or bookmark choice, history entry, back, forward, reload) plus the session state
  becomes the new state, one screen effect and the address-bar text. It composes
  `omnibox.interpret_address`, `forge.locate_forge_file`, `document.visit_location`,
  `document.resolve_link` and the `history` leaves. Other decisions the screen needs
  (bookmark editing and titles, sidebar toggles and pane cycling, Escape, configuration and
  XDG directories, persistence, listing filters, dialog texts, command-line parsing) are their
  own facades; `branding` holds the upstream texts (help document, about box, placeholders,
  confirmation questions).
- `python/frogmouth_ui/` is a thin Textual shell (`app.py`, `dialogs.py`). It builds the
  upstream layout (address bar, sidebar with Contents/Local/Bookmarks/History tabs, viewer,
  footer, modal dialogs), maps upstream's key bindings and widget events to facade calls and
  applies the returned values. It makes no browsing decision of its own. Navigation runs in an
  exclusive worker thread, as upstream's loads ran in exclusive workers.

This keeps every behaviour Cott can describe inside contracts and generated code, while
Textual rendering stays in authored code, as upstream renders with Textual too.

## Parity

| Upstream feature | Status |
| --- | --- |
| CLI `frogmouth [file ...]`, `-h/--help`, `-v/--version`, usage errors | Implemented (`cli.parse_command_line`) |
| Start at the command-line location, else revisit the newest history entry | Implemented (`navigate` Startup) |
| Address bar: http(s) URLs, `~` expansion, existing files and directories, fallback visit | Implemented (`omnibox.interpret_address`) |
| Commands and aliases: about, bookmarks, changelog, chdir, contents, discord, help, history, local, obsidian, quit | Implemented |
| GitHub/GitLab/BitBucket/Codeberg quick view (`owner/repo[:branch] [file]`, main then master probing) | Implemented (`forge.*`) |
| Local and HTTP loading, Markdown suffix check, content-type check, other files and pages handed to the desktop | Implemented (`document.*`) |
| Link following: absolute URLs, relative to a web document, relative to the working directory or the document | Implemented (`document.resolve_link`) |
| Back/forward/reload, history of 256 entries, history pane with delete and clear | Implemented (`history.*`) |
| History, bookmarks and configuration persisted in XDG directories | Implemented |
| Bookmarks: add (Ctrl+D, title dialog), sorted by title, rename (`r`), delete with confirmation | Implemented (`bookmarks.*`) |
| Sidebar: toggling panes, Ctrl+N, tab cycling keys, dock left/right (`\`) persisted | Implemented (`layout.*`, `config.toggle_dock`) |
| Table of contents with jump to heading | Textual widget, wired by the shell |
| Local file browser rooted at home, `chdir`, hidden-entry and Markdown filtering | Implemented (`document.select_browsable_entries`); tree widget from Textual |
| Help (F1) and about (F2) dialogs, links opened externally | Implemented (`branding` texts) |
| Theme toggle (F10) persisted, Escape cascade, `/` and `:` focus, drag-and-drop paste | Implemented |
| Obsidian vault command | Implemented; macOS iCloud path only, as upstream |

### Deviations

- Anchors: `#heading` links scroll within the document and `file.md#heading` links scroll after
  loading (upstream reported an error for local anchors and refetched web pages).
- Only the command word is lower-cased; upstream lower-cased the arguments too, which broke
  `cd` into mixed-case directories and forge file names.
- Deleting a history entry keeps a valid current position; upstream could point past the end.
- Paths are normalized lexically; upstream's `resolve()` also resolved symbolic links.
- Forge probing retries a `405`/`501` answer to HEAD with GET.
- Names in list prompts and dialogs are escaped as Rich markup; broken or unreadable data files
  are reported in a dialog instead of crashing.
- `--help=x` style arguments are reported as unrecognized, and `a -x b` lists only `-x`.
- The Textual version is 6.6.0 instead of 0.41; the displayed version is upstream's `0.9.1`.

## Evidence

The latest `cott check` and `emit python` succeeded. Artifact verification
published a current snapshot with `observed=173 trust_declaration=9 unknown=0
unobserved=0`, but `verify` rejected the strict coverage policy: 76 clauses
across 20 callables are selected, and 8 remain trust declarations. These are
the remote content-type hand-off and storage load/recovery failure branches.
The policy covers navigation, document loading/link resolution, history and
configuration/bookmark/history persistence, with no unobserved, trust-declaration
or unknown allowance. Deployment remains blocked until the selected evidence
meets the policy; artifact `verified=true` alone does not permit deployment.
Seven requirements retain bounded scenario evidence and desktop opening remains
unverified. The current compiler can classify contract `proved` evidence as
`observed`; neither policy selection nor this status establishes all-branch
execution or correctness for arbitrary user files and remote servers.

The TUI was launched in a real tmux pty at `120×36` with scratch XDG directories.
Observed: a local Guide document rendered; Ctrl+Y showed persisted history;
Ctrl+D added a bookmark, `r` renamed it and Delete confirmed removal; Ctrl+T
showed the live heading tree and selected a heading; Ctrl+L displayed the
local file tree, `cd /tmp/fm-smoke/docs` re-rooted it and selecting `guide.md`
opened the document; entering `docs/setup.md` navigated, Ctrl+Left/Right moved
between Guide and Setup, and `history.json` held all three successful visits.
Entering `gh textualize/frogmouth` loaded the live GitHub raw README. F1 and F2
displayed help and about, F10 persisted `"light_mode": true`, and Ctrl+Q quit.
The CLI also printed upstream-style `--help` and `--version` output.
