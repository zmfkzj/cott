from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, _cott_fixture_read
from real.yt_dlp_types import MediaError, MediaError_PluginRejected, PluginDescriptor


def load_plugins(paths: CottList[Path]) -> Result[CottList[PluginDescriptor], MediaError]:
    if len(paths) > 100000:
        return Err(
            error=MediaError_PluginRejected(
                path=paths[100000],
                message="more than 100000 plugins were provided",
            )
        )

    plugins: list[PluginDescriptor] = []
    path: Path
    for path in paths:
        content: str = _cott_fixture_read(path).decode("utf-8-sig")
        extractor_names: list[str] = []
        post_processor_names: list[str] = []
        line: str
        for line in content.splitlines():
            declaration: str = line.strip()
            if declaration == "" or declaration.startswith("#"):
                continue

            kind: str
            separator: str
            name: str
            kind, separator, name = declaration.partition(":")
            name = name.strip()
            if separator == "" or name == "":
                return Err(
                    error=MediaError_PluginRejected(
                        path=path,
                        message="plugin entries must use TYPE:NAME syntax",
                    )
                )
            if kind == "extractor":
                extractor_names.append(name)
            elif kind == "postprocessor" or kind == "post_processor":
                post_processor_names.append(name)
            else:
                return Err(
                    error=MediaError_PluginRejected(
                        path=path,
                        message=f"unsupported plugin entry type: {kind}",
                    )
                )

        if len(extractor_names) == 0 and len(post_processor_names) == 0:
            return Err(
                error=MediaError_PluginRejected(
                    path=path,
                    message="plugin must declare an extractor or postprocessor",
                )
            )
        if path.stem == "":
            return Err(
                error=MediaError_PluginRejected(
                    path=path,
                    message="plugin path must have a name",
                )
            )

        plugins.append(
            PluginDescriptor(
                name=path.stem,
                path=path,
                extractor_names=CottList(values=tuple(extractor_names)),
                post_processor_names=CottList(values=tuple(post_processor_names)),
            )
        )

    return Ok(value=CottList(values=tuple(plugins)))
