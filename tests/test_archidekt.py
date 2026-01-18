from unittest.mock import MagicMock

import pytest

from mtg_print.archidekt import (
    ArchidektError,
    DeckNotFoundError,
    DeckPrivateError,
    extract_deck_id,
    extract_deck_name_from_url,
    fetch_deck,
    is_archidekt_url,
    parse_deck_response,
)


class TestIsArchidektUrl:
    def test_valid_url(self):
        assert is_archidekt_url("https://archidekt.com/decks/1799965/tovolar_werewolves")

    def test_valid_url_without_name(self):
        assert is_archidekt_url("https://archidekt.com/decks/1799965")

    def test_invalid_url(self):
        assert not is_archidekt_url("https://moxfield.com/decks/abc123")

    def test_not_a_url(self):
        assert not is_archidekt_url("deck.txt")


class TestExtractDeckId:
    def test_extracts_id_with_name(self):
        url = "https://archidekt.com/decks/1799965/tovolar_werewolves"
        assert extract_deck_id(url) == "1799965"

    def test_extracts_id_without_name(self):
        url = "https://archidekt.com/decks/365563"
        assert extract_deck_id(url) == "365563"

    def test_extracts_id_with_trailing_slash(self):
        url = "https://archidekt.com/decks/1799965/"
        assert extract_deck_id(url) == "1799965"

    def test_invalid_url_raises_error(self):
        with pytest.raises(ArchidektError, match="Invalid Archidekt URL"):
            extract_deck_id("https://moxfield.com/decks/abc123")


class TestExtractDeckNameFromUrl:
    def test_extracts_name(self):
        url = "https://archidekt.com/decks/1799965/tovolar_werewolves"
        assert extract_deck_name_from_url(url) == "tovolar_werewolves"

    def test_returns_none_without_name(self):
        url = "https://archidekt.com/decks/1799965"
        assert extract_deck_name_from_url(url) is None

    def test_returns_none_for_invalid_url(self):
        url = "https://moxfield.com/decks/abc123"
        assert extract_deck_name_from_url(url) is None


class TestFetchDeck:
    def test_returns_json_on_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "cards": []}
        mock_client.get.return_value = mock_response

        result = fetch_deck("123", client=mock_client)

        assert result == {"id": "123", "cards": []}
        mock_client.get.assert_called_once_with("https://archidekt.com/api/decks/123/")

    def test_raises_not_found_on_404(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        with pytest.raises(DeckNotFoundError, match="Deck not found"):
            fetch_deck("999999", client=mock_client)

    def test_raises_private_on_403(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_client.get.return_value = mock_response

        with pytest.raises(DeckPrivateError, match="Deck is private"):
            fetch_deck("123", client=mock_client)


class TestParseDeckResponse:
    def test_parses_simple_deck(self):
        data = {
            "cards": [
                {
                    "quantity": 4,
                    "card": {
                        "oracleCard": {"name": "Lightning Bolt"},
                        "edition": {"editioncode": "lea"},
                    },
                },
                {
                    "quantity": 2,
                    "card": {
                        "oracleCard": {"name": "Swords to Plowshares"},
                        "edition": {"editioncode": "lea"},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data)

        assert len(decklist.entries) == 2
        assert decklist.entries[0].name == "Lightning Bolt"
        assert decklist.entries[0].count == 4
        assert decklist.entries[0].set_override == "lea"

    def test_parses_dfc_names(self):
        data = {
            "cards": [
                {
                    "quantity": 1,
                    "card": {
                        "oracleCard": {
                            "name": "Delver of Secrets // Insectile Aberration",
                            "layout": "transform",
                        },
                        "edition": {"editioncode": "mid"},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data)

        assert len(decklist.entries) == 1
        assert decklist.entries[0].name == "Delver of Secrets // Insectile Aberration"

    def test_skips_basic_lands_by_default(self):
        data = {
            "cards": [
                {
                    "quantity": 4,
                    "card": {
                        "oracleCard": {"name": "Lightning Bolt"},
                        "edition": {"editioncode": "lea"},
                    },
                },
                {
                    "quantity": 10,
                    "card": {
                        "oracleCard": {"name": "Mountain"},
                        "edition": {"editioncode": "lea"},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data)

        assert len(decklist.entries) == 1
        assert decklist.entries[0].name == "Lightning Bolt"

    def test_includes_basic_lands_when_disabled(self):
        data = {
            "cards": [
                {
                    "quantity": 10,
                    "card": {
                        "oracleCard": {"name": "Mountain"},
                        "edition": {"editioncode": "lea"},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data, skip_basics=False)

        assert len(decklist.entries) == 1
        assert decklist.entries[0].name == "Mountain"

    def test_combines_duplicate_entries(self):
        data = {
            "cards": [
                {
                    "quantity": 2,
                    "card": {
                        "oracleCard": {"name": "Lightning Bolt"},
                        "edition": {"editioncode": "lea"},
                    },
                },
                {
                    "quantity": 2,
                    "card": {
                        "oracleCard": {"name": "Lightning Bolt"},
                        "edition": {"editioncode": "lea"},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data)

        assert len(decklist.entries) == 1
        assert decklist.entries[0].count == 4

    def test_handles_empty_deck(self):
        data = {"cards": []}

        decklist = parse_deck_response(data)

        assert len(decklist.entries) == 0

    def test_handles_missing_edition(self):
        data = {
            "cards": [
                {
                    "quantity": 1,
                    "card": {
                        "oracleCard": {"name": "Sol Ring"},
                        "edition": {},
                    },
                },
            ]
        }

        decklist = parse_deck_response(data)

        assert decklist.entries[0].set_override is None
