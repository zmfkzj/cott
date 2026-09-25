import pathlib

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.core import adapter_descriptors
from real.harlequin.core_types import AdapterKind, CliError, CliError_ConflictingConnectionInputs, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, CliOptions


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _adapter(value: str) -> AdapterKind | None:
    name = _ascii_lower(value)
    for descriptor in adapter_descriptors():
        for scheme in descriptor.uri_schemes:
            if scheme == name:
                return descriptor.kind
    return None


def _canonical(option: str) -> str | None:
    if option in ("--profile", "-P"):
        return "--profile"
    if option in ("--adapter", "-a"):
        return "--adapter"
    if option in ("--query-file", "-f"):
        return "--query-file"
    if option in ("--read-only", "-r"):
        return "--read-only"
    if option == "--no-config":
        return "--no-config"
    return None


def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    args: list[str] = [a for a in arguments]
    profile: str | None = None
    adapter: AdapterKind | None = None
    connection: str | None = None
    query_file: pathlib.Path | None = None
    read_only = False
    no_config = False
    only_positional = False
    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        i += 1
        if only_positional or arg == "-" or not arg.startswith("-"):
            if connection is not None:
                return Err(error=CliError_ConflictingConnectionInputs())
            connection = arg
            continue
        if arg == "--":
            only_positional = True
            continue
        inline: str | None = None
        name = arg
        if arg.startswith("--") and "=" in arg:
            name, _, inline = arg.partition("=")
        option = _canonical(name)
        if option is None:
            return Err(error=CliError_UnknownOption(argument=arg))
        if option == "--read-only" or option == "--no-config":
            if inline is not None:
                return Err(error=CliError_UnknownOption(argument=arg))
            if option == "--read-only":
                read_only = True
            else:
                no_config = True
            continue
        if inline is None:
            if i >= n:
                return Err(error=CliError_MissingOptionValue(option=option))
            inline = args[i]
            i += 1
        if option == "--profile":
            profile = inline
        elif option == "--adapter":
            kind = _adapter(inline)
            if kind is None:
                return Err(error=CliError_InvalidAdapter(value=inline))
            adapter = kind
        else:
            query_file = pathlib.Path(inline)
    if no_config and profile is not None:
        return Err(error=CliError_ConflictingConnectionInputs())
    return Ok(value=CliOptions(
        profile=Some(value=profile) if profile is not None else Nothing(),
        adapter=Some(value=adapter) if adapter is not None else Nothing(),
        connection=Some(value=connection) if connection is not None else Nothing(),
        query_file=Some(value=query_file) if query_file is not None else Nothing(),
        read_only=read_only,
        no_config=no_config,
    ))
