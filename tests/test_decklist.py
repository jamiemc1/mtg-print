import pytest

from mtg_print.decklist import (
    is_basic_land,
    parse_decklist_string,
    parse_line,
    should_ignore_line,
)
from mtg_print.models import DeckEntry


class TestIsBasicLand:
    @pytest.mark.parametrize(
        "name",
        [
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
        ],
    )
    def test_basic_lands_are_detected(self, name: str) -> None:
        assert is_basic_land(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "Tropical Island",
            "Forest of Doom",
            "Breeding Pool",
            "Elvish Reclaimer",
            "Dryad Arbor",
        ],
    )
    def test_non_basics_are_not_detected(self, name: str) -> None:
        assert is_basic_land(name) is False


class TestShouldIgnoreLine:
    @pytest.mark.parametrize(
        "line",
        [
            "Main Deck",
            "Main",
            "Sideboard",
            "Companion",
            "Commander",
            "Creatures(14)",
            "Creatures (14)",
            "Spells(8)",
            "Lands(24)",
            "Planeswalkers(2)",
            "Artifacts(4)",
            "Enchantments(6)",
            "Built with Decked Builder",
            "Exported from Moxfield",
            "Shared via TopDecked MTG",
            "// This is a comment",
            "",
            "   ",
        ],
    )
    def test_ignored_lines(self, line: str) -> None:
        assert should_ignore_line(line) is True

    @pytest.mark.parametrize(
        "line",
        [
            "4 Elvish Reclaimer",
            "1 Forest",
            "4 Lightning Bolt (LEA) 123",
        ],
    )
    def test_card_lines_not_ignored(self, line: str) -> None:
        assert should_ignore_line(line) is False


class TestParseLine:
    def test_simple_format(self) -> None:
        entry = parse_line("4 Elvish Reclaimer")
        assert entry == DeckEntry(count=4, name="Elvish Reclaimer", set_override=None)

    def test_simple_format_with_x(self) -> None:
        entry = parse_line("4x Elvish Reclaimer")
        assert entry == DeckEntry(count=4, name="Elvish Reclaimer", set_override=None)

    def test_moxfield_arena_format(self) -> None:
        entry = parse_line("4 Elvish Reclaimer (MH2) 166")
        assert entry == DeckEntry(count=4, name="Elvish Reclaimer", set_override="MH2")

    def test_manabox_foil_format(self) -> None:
        entry = parse_line("1 Ragavan, Nimble Pilferer (MH2) 138 *F*")
        assert entry == DeckEntry(count=1, name="Ragavan, Nimble Pilferer", set_override="MH2")

    def test_mtggoldfish_format(self) -> None:
        entry = parse_line("4 Lightning Bolt <lea>")
        assert entry == DeckEntry(count=4, name="Lightning Bolt", set_override="lea")

    def test_ignored_line_returns_none(self) -> None:
        assert parse_line("Main Deck") is None
        assert parse_line("Creatures(14)") is None
        assert parse_line("") is None

    def test_whitespace_stripped(self) -> None:
        entry = parse_line("  4 Elvish Reclaimer  ")
        assert entry == DeckEntry(count=4, name="Elvish Reclaimer", set_override=None)


class TestParseDecklistString:
    def test_parses_simple_decklist(self) -> None:
        content = """4 Elvish Reclaimer
4 Knight of the Reliquary
2 Sylvan Library"""
        decklist = parse_decklist_string(content)
        assert len(decklist.entries) == 3
        assert decklist.total_cards == 10

    def test_filters_basic_lands_by_default(self) -> None:
        content = """4 Elvish Reclaimer
4 Forest
4 Plains"""
        decklist = parse_decklist_string(content)
        assert len(decklist.entries) == 1
        assert decklist.entries[0].name == "Elvish Reclaimer"

    def test_includes_basic_lands_when_disabled(self) -> None:
        content = """4 Elvish Reclaimer
4 Forest"""
        decklist = parse_decklist_string(content, skip_basics=False)
        assert len(decklist.entries) == 2
        assert decklist.total_cards == 8

    def test_filters_section_headers(self) -> None:
        content = """Main Deck
Creatures(8)
4 Elvish Reclaimer
4 Knight of the Reliquary

Lands(2)
1 Tropical Island
1 Savannah"""
        decklist = parse_decklist_string(content)
        assert len(decklist.entries) == 4

    def test_mixed_formats(self) -> None:
        content = """4 Elvish Reclaimer
4 Lightning Bolt (LEA) 123
2 Swords to Plowshares <ice>
1x Dark Ritual"""
        decklist = parse_decklist_string(content)
        assert len(decklist.entries) == 4
        assert decklist.entries[0].set_override is None
        assert decklist.entries[1].set_override == "LEA"
        assert decklist.entries[2].set_override == "ice"
        assert decklist.entries[3].set_override is None

    def test_empty_decklist(self) -> None:
        decklist = parse_decklist_string("")
        assert len(decklist.entries) == 0
        assert decklist.total_cards == 0

    def test_decklist_with_only_ignored_lines(self) -> None:
        content = """Main Deck
Sideboard
// Just comments
"""
        decklist = parse_decklist_string(content)
        assert len(decklist.entries) == 0
