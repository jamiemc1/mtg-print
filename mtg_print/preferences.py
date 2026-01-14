import tomllib
from pathlib import Path

import tomli_w

CONFIG_DIR = Path.home() / ".mtg_print"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def load_preferences() -> dict[str, str]:
    if not CONFIG_FILE.exists():
        return {}

    with CONFIG_FILE.open("rb") as f:
        config = tomllib.load(f)

    return config.get("preferences", {})


def save_preference(card_name: str, set_code: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    preferences = load_preferences()
    preferences[card_name] = set_code.lower()

    config = {"preferences": preferences}

    with CONFIG_FILE.open("wb") as f:
        tomli_w.dump(config, f)


def get_preference(card_name: str) -> str | None:
    preferences = load_preferences()
    return preferences.get(card_name)


def clear_preferences() -> int:
    if not CONFIG_FILE.exists():
        return 0

    preferences = load_preferences()
    count = len(preferences)

    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

    return count
