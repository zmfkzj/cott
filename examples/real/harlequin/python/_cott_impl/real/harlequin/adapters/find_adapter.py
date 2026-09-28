from cott_runtime import Nothing, Option, Some

from real.harlequin.adapters import adapter_descriptors
from real.harlequin.adapters_types import AdapterDescriptor


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(char) + 32) if "A" <= char <= "Z" else char for char in text)


def find_adapter(name: str) -> Option[AdapterDescriptor]:
    wanted = _ascii_lower(name)
    for descriptor in adapter_descriptors():
        if _ascii_lower(descriptor.name) == wanted:
            return Some(value=descriptor)
    return Nothing()
