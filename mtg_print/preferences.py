import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

CONFIG_DIR = Path.home() / ".mtg_print"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}

    with CONFIG_FILE.open("rb") as f:
        return tomllib.load(f)


def _save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("wb") as f:
        tomli_w.dump(config, f)


def load_preferences() -> dict[str, str]:
    config = _load_config()
    return config.get("preferences", {})


def save_preference(card_name: str, set_code: str) -> None:
    config = _load_config()
    preferences = config.get("preferences", {})
    preferences[card_name] = set_code.lower()
    config["preferences"] = preferences
    _save_config(config)


def get_preference(card_name: str) -> str | None:
    preferences = load_preferences()
    return preferences.get(card_name)


def get_paper_size() -> str | None:
    config = _load_config()
    settings = config.get("settings", {})
    return settings.get("paper")


def save_paper_size(paper_size: str) -> None:
    config = _load_config()
    settings = config.get("settings", {})
    settings["paper"] = paper_size.lower()
    config["settings"] = settings
    _save_config(config)


@dataclass
class ClearedPreferences:
    card_art_count: int
    paper_size: str | None


def clear_preferences() -> ClearedPreferences:
    if not CONFIG_FILE.exists():
        return ClearedPreferences(card_art_count=0, paper_size=None)

    config = _load_config()
    card_art_count = len(config.get("preferences", {}))
    paper_size = config.get("settings", {}).get("paper")

    CONFIG_FILE.unlink()

    return ClearedPreferences(card_art_count=card_art_count, paper_size=paper_size)
