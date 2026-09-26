from cott_runtime import Nothing, Option, Some

from real.harlequin.export import export_formats


def format_for_path(path: str) -> Option[str]:
    name = path.rsplit("/", 1)[-1]
    dot = name.rfind(".")
    if dot < 0:
        return Nothing()
    suffix = name[dot:]
    for spec in export_formats():
        for extension in spec.extensions:
            if extension == suffix:
                return Some(value=spec.name)
    return Nothing()
