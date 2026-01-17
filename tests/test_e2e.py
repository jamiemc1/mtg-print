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
DECKLIST_FIXTURES = ["modern.txt", "legacy.txt", "commander.txt"]


@pytest.fixture
def client() -> ScryfallClient:
    return ScryfallClient()


@pytest.mark.slow
@pytest.mark.parametrize("fixture", DECKLIST_FIXTURES)
class TestDecklistE2E:
    def test_parses_and_fetches_all_cards(self, client: ScryfallClient, fixture: str) -> None:
        decklist = parse_decklist(FIXTURES_DIR / fixture)
        format_name = fixture.replace(".txt", "").title()

        start = time.perf_counter()
        for entry in decklist.entries:
            printing = client.get_card_by_name(entry.name)
            # DFCs: entry.name (front face) is contained in printing.name ("Front // Back")
            assert entry.name in printing.name
            assert len(printing.faces) >= 1
        elapsed = time.perf_counter() - start

        print(f"\n{format_name}: fetched {len(decklist.entries)} cards in {elapsed:.2f}s")

    def test_collects_related_parts(self, client: ScryfallClient, fixture: str) -> None:
        decklist = parse_decklist(FIXTURES_DIR / fixture)
        format_name = fixture.replace(".txt", "").title()
        all_parts: dict[str, str] = {}

        start = time.perf_counter()
        for entry in decklist.entries:
            for part in client.get_related_parts(entry.name):
                all_parts[part.name] = part.layout
        elapsed = time.perf_counter() - start

        print(f"\n{format_name}: found {len(all_parts)} related parts in {elapsed:.2f}s")
        for name, layout in sorted(all_parts.items()):
            print(f"  - {name} ({layout})")
