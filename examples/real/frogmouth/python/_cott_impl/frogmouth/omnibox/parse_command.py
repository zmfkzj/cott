from cott_runtime import Nothing, Option, Some
from frogmouth.model_types import Forge_BitBucket, Forge_Codeberg, Forge_GitHub, Forge_GitLab
from frogmouth.omnibox_types import OmniboxCommand, OmniboxCommand_About, OmniboxCommand_Bookmarks, OmniboxCommand_ChangeDirectory, OmniboxCommand_Changelog, OmniboxCommand_Contents, OmniboxCommand_Discord, OmniboxCommand_Forge, OmniboxCommand_Help, OmniboxCommand_History, OmniboxCommand_Local, OmniboxCommand_Obsidian, OmniboxCommand_Quit


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _canonical(word: str) -> str:
    aliases: dict[str, str] = {
        "a": "about", "b": "bookmarks", "bm": "bookmarks", "bb": "bitbucket",
        "c": "contents", "toc": "contents", "cb": "codeberg", "cd": "chdir",
        "cl": "changelog", "gh": "github", "gl": "gitlab", "h": "history",
        "l": "local", "obs": "obsidian", "q": "quit", "?": "help",
    }
    return aliases.get(word, word)


def parse_command(value: str) -> Option[OmniboxCommand]:
    parts = value.split(None, 1)
    if not parts:
        return Nothing()
    word = _canonical(_ascii_lower(parts[0]))
    arguments = parts[1].strip() if len(parts) > 1 else ""
    if word == "about":
        return Some(value=OmniboxCommand_About())
    if word == "bookmarks":
        return Some(value=OmniboxCommand_Bookmarks())
    if word == "changelog":
        return Some(value=OmniboxCommand_Changelog())
    if word == "contents":
        return Some(value=OmniboxCommand_Contents())
    if word == "discord":
        return Some(value=OmniboxCommand_Discord())
    if word == "help":
        return Some(value=OmniboxCommand_Help())
    if word == "history":
        return Some(value=OmniboxCommand_History())
    if word == "local":
        return Some(value=OmniboxCommand_Local())
    if word == "quit":
        return Some(value=OmniboxCommand_Quit())
    if word == "chdir":
        return Some(value=OmniboxCommand_ChangeDirectory(target=arguments))
    if word == "obsidian":
        return Some(value=OmniboxCommand_Obsidian(vault=arguments))
    if word == "github":
        return Some(value=OmniboxCommand_Forge(forge=Forge_GitHub(), arguments=arguments))
    if word == "gitlab":
        return Some(value=OmniboxCommand_Forge(forge=Forge_GitLab(), arguments=arguments))
    if word == "bitbucket":
        return Some(value=OmniboxCommand_Forge(forge=Forge_BitBucket(), arguments=arguments))
    if word == "codeberg":
        return Some(value=OmniboxCommand_Forge(forge=Forge_Codeberg(), arguments=arguments))
    return Nothing()
