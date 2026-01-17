"""End-to-end tests using real decklists against Scryfall API.

These tests hit the real Scryfall API and are marked as slow.
Run with: pytest tests/test_e2e.py -v -s -m slow
Skip with: pytest tests/ -v (default)
"""

import time
from pathlib import Path

import pytest

from mtg_print.decklist import parse_decklist
from mtg_print.scryfall import ScryfallClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def client() -> ScryfallClient:
    return ScryfallClient()


@pytest.mark.slow
class TestModernDecklist:
    def test_parses_and_fetches_all_cards(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "modern.txt")

        start = time.perf_counter()
        for entry in decklist.entries:
            printing = client.get_card_by_name(entry.name)
            assert entry.name in printing.name
            assert len(printing.faces) >= 1
        elapsed = time.perf_counter() - start

        print(f"\nModern: fetched {len(decklist.entries)} cards in {elapsed:.2f}s")

    def test_collects_related_parts(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "modern.txt")
        all_parts: dict[str, str] = {}

        start = time.perf_counter()
        for entry in decklist.entries:
            for part in client.get_related_parts(entry.name):
                all_parts[part.name] = part.layout
        elapsed = time.perf_counter() - start

        print(f"\nModern: found {len(all_parts)} related parts in {elapsed:.2f}s")
        for name, layout in sorted(all_parts.items()):
            print(f"  - {name} ({layout})")


@pytest.mark.slow
class TestLegacyDecklist:
    def test_parses_and_fetches_all_cards(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "legacy.txt")

        start = time.perf_counter()
        for entry in decklist.entries:
            printing = client.get_card_by_name(entry.name)
            assert entry.name in printing.name
            assert len(printing.faces) >= 1
        elapsed = time.perf_counter() - start

        print(f"\nLegacy: fetched {len(decklist.entries)} cards in {elapsed:.2f}s")

    def test_collects_related_parts(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "legacy.txt")
        all_parts: dict[str, str] = {}

        start = time.perf_counter()
        for entry in decklist.entries:
            for part in client.get_related_parts(entry.name):
                all_parts[part.name] = part.layout
        elapsed = time.perf_counter() - start

        print(f"\nLegacy: found {len(all_parts)} related parts in {elapsed:.2f}s")
        for name, layout in sorted(all_parts.items()):
            print(f"  - {name} ({layout})")


@pytest.mark.slow
class TestCommanderDecklist:
    def test_parses_and_fetches_all_cards(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "commander.txt")

        start = time.perf_counter()
        for entry in decklist.entries:
            printing = client.get_card_by_name(entry.name)
            assert entry.name in printing.name
            assert len(printing.faces) >= 1
        elapsed = time.perf_counter() - start

        print(f"\nCommander: fetched {len(decklist.entries)} cards in {elapsed:.2f}s")

    def test_collects_related_parts(self, client: ScryfallClient) -> None:
        decklist = parse_decklist(FIXTURES_DIR / "commander.txt")
        all_parts: dict[str, str] = {}

        start = time.perf_counter()
        for entry in decklist.entries:
            for part in client.get_related_parts(entry.name):
                all_parts[part.name] = part.layout
        elapsed = time.perf_counter() - start

        print(f"\nCommander: found {len(all_parts)} related parts in {elapsed:.2f}s")
        for name, layout in sorted(all_parts.items()):
            print(f"  - {name} ({layout})")
