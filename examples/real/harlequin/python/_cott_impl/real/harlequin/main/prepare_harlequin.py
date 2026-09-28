import os
import sys
from pathlib import Path

from cott_runtime import CottList, Err, FrozenMap, Nothing, Option, Some
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from real.harlequin.adapters import adapter_descriptors, adapter_options, find_adapter
from real.harlequin.app_types import IdeContext
from real.harlequin.cli import first_pass, harlequin_help, harlequin_version_text, parse_harlequin_arguments, resolve_harlequin_settings
from real.harlequin.config import config_search_paths, interpolate_profile, merge_config_files, read_config_file, select_profile
from real.harlequin.config_types import ConfigEntry, ConfigFile, ConfigValue_Array, ConfigValue_Text, Profile
from real.harlequin.history import harlequin_paths
from real.harlequin.keymap import bind_keymaps, builtin_keymaps
from real.harlequin.keymap_types import KeymapError, KeymapError_UnknownAction, KeymapError_UnknownKeymap
from real.harlequin.main_types import LaunchPlan, LaunchPlan_Exit, LaunchPlan_Ide
from real.harlequin.results_types import NumberFormat
from real.harlequin.style import find_theme, theme_palettes
from real.harlequin.support import apply_locale, open_ssh_tunnel
from real.harlequin.support_types import SshTunnel
from real.harlequin.tools import run_config_wizard, run_keys_app


def _error(title: str, message: str) -> LaunchPlan:
    if sys.stderr.isatty():
        Console(file=sys.stderr).print(Panel(Text(message), title=Text(title), border_style="red"))
    else:
        sys.stderr.write(f"{title}\n\n{message}\n")
    return LaunchPlan_Exit(status=2)


def _keymap_error(error: KeymapError) -> str:
    if isinstance(error, KeymapError_UnknownKeymap):
        return f"No keymap found with name {error.name}."
    if isinstance(error, KeymapError_UnknownAction):
        return f"Keymap {error.keymap} defines an unknown action: {error.action}."
    return f"Keymap {error.keymap} defines an empty key for action {error.action}."


def _keymap_names(entries: CottList[ConfigEntry]) -> Option[CottList[str]]:
    for entry in entries:
        if entry.key == "keymap_name":
            value = entry.value
            if isinstance(value, ConfigValue_Text):
                return Some(value=CottList(values=[value.value]))
            if isinstance(value, ConfigValue_Array):
                names: list[str] = []
                for item in value.values:
                    if not isinstance(item, ConfigValue_Text):
                        return Nothing()
                    names.append(item.value)
                return Some(value=CottList(values=names))
    return Nothing()


def prepare_harlequin(arguments: CottList[str]) -> LaunchPlan:
    scanned = first_pass(arguments)
    environment = FrozenMap(values=dict(os.environ))
    home = Path.home()
    paths = harlequin_paths(sys.platform, home, environment)
    explicit_path: Option[Path] = Nothing()
    if isinstance(scanned.config_path, Some):
        explicit_path = Some(value=Path(scanned.config_path.value))
    else:
        env_path = os.environ.get("HARLEQUIN_CONFIG_PATH")
        if env_path:
            explicit_path = Some(value=Path(env_path))
    search_paths = config_search_paths(explicit_path, Path.cwd(), paths.config_dir, home)
    files: list[ConfigFile] = []
    first_existing: Path | None = None
    for path in search_paths:
        if first_existing is None and path.exists():
            first_existing = path
        read = read_config_file(path)
        if isinstance(read, Err):
            return _error(read.error.title, read.error.message)
        if isinstance(read.value, Some):
            files.append(read.value.value)
    merged = merge_config_files(CottList(values=files))

    adapter_name = "duckdb"
    if isinstance(scanned.adapter, Some):
        adapter_name = scanned.adapter.value
    else:
        requested: Option[str] = scanned.profile if isinstance(scanned.profile, Some) else merged.default_profile
        if isinstance(requested, Some) and requested.value != "None":
            for candidate in merged.profiles:
                if candidate.name == requested.value:
                    for entry in candidate.entries:
                        if entry.key == "adapter" and isinstance(entry.value, ConfigValue_Text):
                            adapter_name = entry.value.value
                    break
    descriptors = adapter_descriptors()
    names = CottList(values=[descriptor.name for descriptor in descriptors])
    found = find_adapter(adapter_name)
    if not isinstance(found, Some):
        return _error("Harlequin could not load your adapter.", f"No adapter found with name {adapter_name}. Installed adapters: {', '.join(sorted(names))}.")
    descriptor = found.value
    options = adapter_options(descriptor.kind)
    parsed_result = parse_harlequin_arguments(arguments, names, options)
    if isinstance(parsed_result, Err):
        sys.stderr.write("Usage: harlequin [OPTIONS] [CONN_STR]...\nTry 'harlequin --help' for help.\n\n" + f"Error: {parsed_result.error.message}\n")
        return LaunchPlan_Exit(status=2)
    parsed = parsed_result.value
    if parsed.show_version:
        sys.stdout.write(harlequin_version_text(names))
        return LaunchPlan_Exit(status=0)
    if parsed.show_help:
        sys.stdout.write(harlequin_help(descriptors))
        return LaunchPlan_Exit(status=0)

    base_keymaps = builtin_keymaps()
    builtin_names = CottList(values=[keymap.name for keymap in base_keymaps])
    available = CottList(values=[*base_keymaps, *merged.keymaps])
    typed_path: Option[Path] = Nothing()
    if isinstance(parsed.config_path, Some):
        typed_path = Some(value=Path(parsed.config_path.value))
    if parsed.run_config_wizard:
        return LaunchPlan_Exit(status=run_config_wizard(
            typed_path,
            first_existing if first_existing is not None else Path(".harlequin.toml"),
            descriptors,
            CottList(values=[palette.name for palette in theme_palettes()]),
            CottList(values=[keymap.name for keymap in available]),
        ))

    selected = select_profile(merged, parsed.profile)
    if isinstance(selected, Err):
        return _error(selected.error.title, selected.error.message)
    profile: Option[Profile] = selected.value
    if isinstance(profile, Some):
        source: Option[str] = Nothing()
        for supplied in merged.sources:
            if supplied.name == profile.value.name:
                source = Some(value=supplied.path)
                break
        interpolated = interpolate_profile(profile.value, environment, source)
        if isinstance(interpolated, Err):
            return _error(interpolated.error.title, interpolated.error.message)
        profile = Some(value=interpolated.value)

    if parsed.run_keys_app:
        save_path = first_existing if first_existing is not None else paths.config_dir / "config.toml"
        if isinstance(typed_path, Some):
            save_path = typed_path.value
        active = _keymap_names(parsed.explicit)
        if not isinstance(active, Some) and isinstance(profile, Some):
            active = _keymap_names(profile.value.entries)
        active_names = active.value if isinstance(active, Some) else CottList(values=["vscode"])
        return LaunchPlan_Exit(status=run_keys_app(save_path, active_names, builtin_names, available))

    resolved = resolve_harlequin_settings(profile, parsed, descriptor, options)
    if isinstance(resolved, Err):
        return _error(resolved.error.title, resolved.error.message)
    settings = resolved.value
    localized = apply_locale(settings.locale)
    if isinstance(localized, Err):
        return _error("Harlequin could not set your locale.", localized.error.message)
    outcome = localized.value
    if isinstance(outcome.warning, Some):
        sys.stderr.write(outcome.warning.value + "\n")
    number_format = NumberFormat(thousands_separator=outcome.thousands_separator, decimal_point=outcome.decimal_point, grouping=outcome.grouping)
    themed = find_theme(settings.theme)
    if isinstance(themed, Err):
        return _error("Harlequin couldn't load your theme.", f"No theme found with name {themed.error.name}.")
    bound = bind_keymaps(available, settings.keymap_names)
    if isinstance(bound, Err):
        return _error("Harlequin couldn't load your keymap.", _keymap_error(bound.error))
    tunnel: Option[SshTunnel] = Nothing()
    if isinstance(settings.ssh, Some):
        opened = open_ssh_tunnel(settings.ssh.value)
        if isinstance(opened, Err):
            return _error("Harlequin could not open the SSH tunnel.", opened.error.message)
        tunnel = Some(value=opened.value)
        for warning in opened.value.warnings:
            sys.stderr.write(warning + "\n")
    return LaunchPlan_Ide(settings=settings, context=IdeContext(descriptor=descriptor, paths=paths, palette=themed.value, number_format=number_format, tunnel=tunnel, environment=environment), keymaps=merged.keymaps)
