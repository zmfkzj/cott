from cott_runtime import CottList
from real.yt_dlp_types import ExtractorDescriptor


def discover_extractors() -> CottList[ExtractorDescriptor]:
    return CottList(
        values=(
            ExtractorDescriptor(
                name="youtube",
                urls=CottList(
                    values=(
                        "https://www.youtube.com/",
                        "https://youtu.be/",
                    )
                ),
                enabled=True,
                requires_login=False,
            ),
            ExtractorDescriptor(
                name="vimeo",
                urls=CottList(values=("https://vimeo.com/",)),
                enabled=True,
                requires_login=False,
            ),
            ExtractorDescriptor(
                name="soundcloud",
                urls=CottList(values=("https://soundcloud.com/",)),
                enabled=True,
                requires_login=False,
            ),
            ExtractorDescriptor(
                name="twitch",
                urls=CottList(values=("https://www.twitch.tv/",)),
                enabled=True,
                requires_login=False,
            ),
            ExtractorDescriptor(
                name="generic",
                urls=CottList(values=("http://", "https://")),
                enabled=True,
                requires_login=False,
            ),
        )
    )
