from frogmouth.config_types import Config, Theme_Dark, Theme_Light


def toggle_theme(config: Config) -> Config:
    new_theme = Theme_Light() if isinstance(config.theme, Theme_Dark) else Theme_Dark()
    return Config(theme=new_theme, markdown_extensions=config.markdown_extensions, navigation_dock=config.navigation_dock)
