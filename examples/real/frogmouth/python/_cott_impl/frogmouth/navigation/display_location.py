from frogmouth.model_types import Location


def display_location(location: Location) -> str:
    return location.target or "Frogmouth"
