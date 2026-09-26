import os
from typing import Final, cast

import babel
import babel.numbers
from cott_runtime import Err, Nothing, Ok, Option, Result, Some, CottList, U64

from real.harlequin.support_types import LocaleError, LocaleError_Unavailable, LocaleOutcome

_URL: Final[str] = "https://harlequin.sh/docs/troubleshooting/locale"


def _is_c(name: str) -> bool:
    base = name.split(".", 1)[0]
    return name in ("C", "POSIX") or base in ("C", "POSIX")


def _c_outcome(warning: Option[str]) -> LocaleOutcome:
    return LocaleOutcome(thousands_separator="", decimal_point=".", grouping=CottList(values=[]), warning=warning)


def _parse(name: str) -> babel.Locale | None:
    stripped = name.split(".", 1)[0].split("@", 1)[0]
    try:
        return babel.Locale.parse(stripped, sep="_")
    except (ValueError, babel.UnknownLocaleError):
        return None


def _outcome(loc: babel.Locale, warning: Option[str]) -> LocaleOutcome:
    pattern = loc.decimal_formats[None]
    raw = cast(tuple[int, int], pattern.grouping)
    primary = int(raw[0])
    secondary = int(raw[1])
    values: list[U64] = [primary] if primary == secondary else [primary, secondary]
    return LocaleOutcome(
        thousands_separator=babel.numbers.get_group_symbol(loc),
        decimal_point=babel.numbers.get_decimal_symbol(loc),
        grouping=CottList(values=values),
        warning=warning,
    )


def _env_name() -> str:
    for key in ("LC_ALL", "LC_NUMERIC", "LANG"):
        value = os.environ.get(key, "")
        if value:
            return value
    return "C"


def apply_locale(requested: Option[str]) -> Result[LocaleOutcome, LocaleError]:
    if isinstance(requested, Some):
        name = requested.value
        if _is_c(name):
            return Ok(value=_c_outcome(Nothing()))
        loc = _parse(name)
        if loc is None:
            err: LocaleError = LocaleError_Unavailable(
                message=f"unsupported locale setting: You likely need to install the locale {name} on your OS."
            )
            return Err(error=err)
        return Ok(value=_outcome(loc, Nothing()))
    name = _env_name()
    if _is_c(name):
        fallback = _parse("en_US")
        if fallback is None:
            return Ok(
                value=_c_outcome(
                    Some(
                        value=(
                            "Harlequin could not set a locale with thousands separators. "
                            f"Your device's locale is set to {name}, and en_US.UTF-8 is unavailable, "
                            "so numbers will be shown without thousands separators. "
                            "To configure a different locale, pass a locale string to Harlequin "
                            "using the --locale option. To suppress this warning, run Harlequin "
                            f"with the --locale C option. See also {_URL}"
                        )
                    )
                )
            )
        return Ok(
            value=_outcome(
                fallback,
                Some(
                    value=(
                        "Harlequin uses the locale of your device to format numbers. "
                        f"Your device's locale is set to {name}, which is a POSIX locale for "
                        "computers, not humans. We assume you are a human and want to see "
                        "thousands separators, so we set your locale to en_US.UTF-8. To configure "
                        "a different locale or to suppress this warning, set your system locale, "
                        "or pass a locale string to Harlequin using the --locale option. To use "
                        "Harlequin with the C locale, run Harlequin with the --locale C option. "
                        f"See also {_URL}"
                    )
                ),
            )
        )
    loc = _parse(name)
    if loc is None:
        return Ok(value=_c_outcome(Nothing()))
    return Ok(value=_outcome(loc, Nothing()))
