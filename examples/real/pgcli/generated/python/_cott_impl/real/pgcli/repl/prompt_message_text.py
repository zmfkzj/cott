from cott_runtime import Option, Some
from real.pgcli.repl import render_prompt
from real.pgcli.repl_types import PromptInfo


def prompt_message_text(prompt_format: str, prompt_dsn_format: Option[str], info: PromptInfo) -> str:
    template = prompt_format
    if info.dsn_alias and isinstance(prompt_dsn_format, Some):
        template = prompt_dsn_format.value
    text = render_prompt(template, info)
    if template == "\\u@\\h:\\d> " and len(text) > 30:
        text = render_prompt("\\d> ", info)
    return text.replace("\\x1b", "\x1b")
