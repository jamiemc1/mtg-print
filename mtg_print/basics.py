BASIC_LANDS = {
    "Forest",
    "Island",
    "Plains",
    "Mountain",
    "Swamp",
    "Wastes",
    "Snow-Covered Forest",
    "Snow-Covered Island",
    "Snow-Covered Plains",
    "Snow-Covered Mountain",
    "Snow-Covered Swamp",
    "Snow-Covered Wastes",
}


def is_basic_land(name: str) -> bool:
    return name in BASIC_LANDS
