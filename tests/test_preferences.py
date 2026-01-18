from unittest.mock import patch

import pytest

from mtg_print.preferences import (
    ClearedPreferences,
    clear_preferences,
    get_paper_size,
    get_preference,
    load_preferences,
    save_paper_size,
    save_preference,
)


@pytest.fixture
def prefs_dir(tmp_path):
    config_dir = tmp_path / ".mtg_print"
    config_file = config_dir / "config.toml"
    with (
        patch("mtg_print.preferences.CONFIG_DIR", config_dir),
        patch("mtg_print.preferences.CONFIG_FILE", config_file),
    ):
        yield config_dir, config_file


class TestLoadPreferences:
    def test_returns_empty_dict_when_no_config(self, prefs_dir) -> None:
        result = load_preferences()

        assert result == {}

    def test_loads_existing_preferences(self, prefs_dir) -> None:
        config_dir, config_file = prefs_dir
        config_dir.mkdir(parents=True)
        config_file.write_text('[preferences]\n"Elvish Reclaimer" = "mh1"\n')

        result = load_preferences()

        assert result == {"Elvish Reclaimer": "mh1"}

    def test_returns_empty_dict_when_no_preferences_section(self, prefs_dir) -> None:
        config_dir, config_file = prefs_dir
        config_dir.mkdir(parents=True)
        config_file.write_text("[other]\nkey = 'value'\n")

        result = load_preferences()

        assert result == {}


class TestSavePreference:
    def test_creates_config_dir_and_file(self, prefs_dir) -> None:
        config_dir, config_file = prefs_dir

        save_preference("Scavenging Ooze", "M14")

        assert config_dir.exists()
        assert config_file.exists()

    def test_saves_preference_lowercase(self, prefs_dir) -> None:
        save_preference("Scavenging Ooze", "M14")

        result = load_preferences()
        assert result["Scavenging Ooze"] == "m14"

    def test_preserves_existing_preferences(self, prefs_dir) -> None:
        save_preference("Card One", "SET1")
        save_preference("Card Two", "SET2")

        result = load_preferences()
        assert result == {"Card One": "set1", "Card Two": "set2"}

    def test_overwrites_existing_preference_for_same_card(self, prefs_dir) -> None:
        save_preference("Elvish Reclaimer", "MH1")
        save_preference("Elvish Reclaimer", "MH2")

        result = load_preferences()
        assert result["Elvish Reclaimer"] == "mh2"


class TestGetPreference:
    def test_returns_none_when_no_preference(self, prefs_dir) -> None:
        result = get_preference("Unknown Card")

        assert result is None

    def test_returns_saved_preference(self, prefs_dir) -> None:
        save_preference("Sylvan Library", "LEG")

        result = get_preference("Sylvan Library")
        assert result == "leg"

    def test_returns_none_for_different_card(self, prefs_dir) -> None:
        save_preference("Sylvan Library", "LEG")

        result = get_preference("Other Card")
        assert result is None


class TestClearPreferences:
    def test_returns_empty_when_no_config(self, prefs_dir) -> None:
        result = clear_preferences()

        assert result == ClearedPreferences(card_art_count=0, paper_size=None)

    def test_returns_count_of_cleared_card_preferences(self, prefs_dir) -> None:
        save_preference("Card One", "SET1")
        save_preference("Card Two", "SET2")
        save_preference("Card Three", "SET3")

        result = clear_preferences()

        assert result.card_art_count == 3

    def test_returns_cleared_paper_size(self, prefs_dir) -> None:
        save_paper_size("letter")

        result = clear_preferences()

        assert result.paper_size == "letter"

    def test_returns_both_card_and_paper_preferences(self, prefs_dir) -> None:
        save_preference("Card One", "SET1")
        save_paper_size("letter")

        result = clear_preferences()

        assert result.card_art_count == 1
        assert result.paper_size == "letter"

    def test_removes_config_file(self, prefs_dir) -> None:
        config_dir, config_file = prefs_dir
        save_preference("Test Card", "TST")

        assert config_file.exists()

        clear_preferences()

        assert not config_file.exists()

    def test_preferences_empty_after_clear(self, prefs_dir) -> None:
        save_preference("Test Card", "TST")
        clear_preferences()

        result = load_preferences()
        assert result == {}


class TestGetPaperSize:
    def test_returns_none_when_no_config(self, prefs_dir) -> None:
        result = get_paper_size()

        assert result is None

    def test_returns_none_when_no_settings_section(self, prefs_dir) -> None:
        save_preference("Card", "SET")

        result = get_paper_size()

        assert result is None

    def test_returns_saved_paper_size(self, prefs_dir) -> None:
        save_paper_size("letter")

        result = get_paper_size()

        assert result == "letter"


class TestSavePaperSize:
    def test_creates_config_dir_and_file(self, prefs_dir) -> None:
        config_dir, config_file = prefs_dir

        save_paper_size("letter")

        assert config_dir.exists()
        assert config_file.exists()

    def test_saves_paper_size_lowercase(self, prefs_dir) -> None:
        save_paper_size("LETTER")

        result = get_paper_size()
        assert result == "letter"

    def test_preserves_existing_card_preferences(self, prefs_dir) -> None:
        save_preference("Card One", "SET1")
        save_paper_size("letter")

        result = load_preferences()
        assert result == {"Card One": "set1"}

    def test_overwrites_existing_paper_size(self, prefs_dir) -> None:
        save_paper_size("a4")
        save_paper_size("letter")

        result = get_paper_size()
        assert result == "letter"
