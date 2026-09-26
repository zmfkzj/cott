from frogmouth.config_types import Config, Dock_Left, Dock_Right


def toggle_dock(config: Config) -> Config:
    new_dock = Dock_Right() if isinstance(config.navigation_dock, Dock_Left) else Dock_Left()
    return Config(theme=config.theme, markdown_extensions=config.markdown_extensions, navigation_dock=new_dock)
