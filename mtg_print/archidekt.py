import re

import httpx

from mtg_print.basics import is_basic_land
from mtg_print.models import DeckEntry, Decklist

ARCHIDEKT_API_BASE = "https://archidekt.com/api/decks"
ARCHIDEKT_URL_PATTERN = re.compile(r"archidekt\.com/decks/(\d+)(?:/([^/?]+))?")


class ArchidektError(Exception):
    pass


class DeckNotFoundError(ArchidektError):
    pass


class DeckPrivateError(ArchidektError):
    pass


def extract_deck_id(url: str) -> str:
    match = ARCHIDEKT_URL_PATTERN.search(url)
    if not match:
        raise ArchidektError(f"Invalid Archidekt URL: {url}")
    return match.group(1)


def extract_deck_name_from_url(url: str) -> str | None:
    match = ARCHIDEKT_URL_PATTERN.search(url)
    if match and match.group(2):
        return match.group(2)
    return None


def is_archidekt_url(url: str) -> bool:
    return "archidekt.com/decks/" in url


def fetch_deck(deck_id: str, client: httpx.Client | None = None) -> dict:
    should_close = client is None
    if client is None:
        client = httpx.Client(timeout=30.0)

    try:
        response = client.get(f"{ARCHIDEKT_API_BASE}/{deck_id}/")

        if response.status_code == 404:
            raise DeckNotFoundError(f"Deck not found: {deck_id}")
        if response.status_code == 403:
            raise DeckPrivateError(f"Deck is private: {deck_id}")

        response.raise_for_status()
        return response.json()
    finally:
        if should_close:
            client.close()


def parse_deck_response(data: dict, skip_basics: bool = True) -> Decklist:
    entries: list[DeckEntry] = []
    seen_names: dict[str, int] = {}

    for card_data in data.get("cards", []):
        card_info = card_data.get("card", {})
        oracle_card = card_info.get("oracleCard", {})

        name = oracle_card.get("name")
        if not name:
            continue

        quantity = card_data.get("quantity", 1)

        if skip_basics and is_basic_land(name):
            continue

        edition = card_info.get("edition", {})
        set_code = edition.get("editioncode")

        if name in seen_names:
            entries[seen_names[name]].count += quantity
        else:
            seen_names[name] = len(entries)
            entries.append(DeckEntry(count=quantity, name=name, set_override=set_code))

    return Decklist(entries=entries)


def fetch_decklist(url: str, skip_basics: bool = True) -> Decklist:
    deck_id = extract_deck_id(url)
    data = fetch_deck(deck_id)
    return parse_deck_response(data, skip_basics=skip_basics)
