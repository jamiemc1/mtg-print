from datetime import date

import pytest

from mtg_print.models import CardFace, CardPrinting, DeckEntry, Decklist


class TestCardPrinting:
    @pytest.mark.parametrize(
        "layout,expected",
        [
            ("transform", True),
            ("modal_dfc", True),
            ("reversible_card", True),
            ("normal", False),
            ("adventure", False),
            ("split", False),
        ],
    )
    def test_is_double_faced(self, layout: str, expected: bool) -> None:
        printing = CardPrinting(
            name="Test",
            set_code="tst",
            set_name="Test Set",
            collector_number="1",
            release_date=date(2020, 1, 1),
            scryfall_uri="https://scryfall.com/card/tst/1",
            layout=layout,
            faces=[],
        )
        assert printing.is_double_faced is expected

    def test_front_image(self) -> None:
        printing = CardPrinting(
            name="Test",
            set_code="tst",
            set_name="Test Set",
            collector_number="1",
            release_date=date(2020, 1, 1),
            scryfall_uri="https://scryfall.com/card/tst/1",
            layout="normal",
            faces=[CardFace(name="Test", image_uri_png="https://example.com/front.png")],
        )
        assert printing.front_image == "https://example.com/front.png"

    def test_back_image_when_present(self) -> None:
        printing = CardPrinting(
            name="Test // Back",
            set_code="tst",
            set_name="Test Set",
            collector_number="1",
            release_date=date(2020, 1, 1),
            scryfall_uri="https://scryfall.com/card/tst/1",
            layout="transform",
            faces=[
                CardFace(name="Test", image_uri_png="https://example.com/front.png"),
                CardFace(name="Back", image_uri_png="https://example.com/back.png"),
            ],
        )
        assert printing.back_image == "https://example.com/back.png"

    def test_back_image_when_absent(self) -> None:
        printing = CardPrinting(
            name="Test",
            set_code="tst",
            set_name="Test Set",
            collector_number="1",
            release_date=date(2020, 1, 1),
            scryfall_uri="https://scryfall.com/card/tst/1",
            layout="normal",
            faces=[CardFace(name="Test", image_uri_png="https://example.com/front.png")],
        )
        assert printing.back_image is None


class TestDecklist:
    def test_total_cards_empty(self) -> None:
        decklist = Decklist(entries=[])
        assert decklist.total_cards == 0

    def test_total_cards_single_entry(self) -> None:
        decklist = Decklist(entries=[DeckEntry(count=4, name="Lightning Bolt")])
        assert decklist.total_cards == 4

    def test_total_cards_multiple_entries(self) -> None:
        decklist = Decklist(
            entries=[
                DeckEntry(count=4, name="Lightning Bolt"),
                DeckEntry(count=4, name="Elvish Reclaimer"),
                DeckEntry(count=2, name="Sylvan Library"),
            ]
        )
        assert decklist.total_cards == 10


class TestDeckEntry:
    def test_set_override_optional(self) -> None:
        entry = DeckEntry(count=4, name="Test Card")
        assert entry.set_override is None

    def test_set_override_provided(self) -> None:
        entry = DeckEntry(count=4, name="Test Card", set_override="MH1")
        assert entry.set_override == "MH1"
