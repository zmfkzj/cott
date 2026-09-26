from cott_runtime import Nothing, Some

from real.harlequin.adapters import adapter_descriptors
from real.harlequin.adapters_types import AdapterDescriptor


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def find_adapter(name: str) -> Some[AdapterDescriptor] | Nothing:
    wanted = _ascii_lower(name)
    for descriptor in adapter_descriptors():
        if _ascii_lower(descriptor.name) == wanted:
            return Some(value=descriptor)
    return Nothing()
