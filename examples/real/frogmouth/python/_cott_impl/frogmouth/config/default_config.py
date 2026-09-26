from cott_runtime import CottList

from frogmouth.config_types import Config, Dock_Left, Theme_Dark


def default_config() -> Config:
    return Config(theme=Theme_Dark(), markdown_extensions=CottList(values=[".md", ".markdown"]), navigation_dock=Dock_Left())
