import re
from pathlib import Path

from mtg_print.models import DeckEntry, Decklist

PATTERNS = [
    re.compile(
        r"^(\d+)x?\s+(.+?)\s*\((\w+)\)\s*\d*\s*(?:\*F\*)?$"
    ),  # Moxfield/Arena/Manabox: 4 Card (SET) 123 *F*
    re.compile(r"^(\d+)x?\s+(.+?)\s*<(\w+)>$"),  # MTGGoldfish: 4 Card <set>
    re.compile(r"^(\d+)x?\s+(.+?)$"),  # Simple: 4 Card or 4x Card
]

IGNORE_PATTERNS = [
    re.compile(r"^(Main|Main Deck|Sideboard|Companion|Commander)", re.IGNORECASE),
    re.compile(r"^(Creatures?|Spells?|Lands?|Planeswalkers?|Artifacts?|Enchantments?)\s*\(\d+\)"),
    re.compile(r"^(Built with|Exported from|Shared via|//)"),
    re.compile(r"^\s*$"),
]

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


def should_ignore_line(line: str) -> bool:
    return any(p.match(line) for p in IGNORE_PATTERNS)


def parse_line(line: str) -> DeckEntry | None:
    line = line.strip()
    if should_ignore_line(line):
        return None

    for pattern in PATTERNS:
        if match := pattern.match(line):
            groups = match.groups()
            count = int(groups[0])
            name = groups[1].strip()
            set_code = groups[2] if len(groups) > 2 else None
            return DeckEntry(count=count, name=name, set_override=set_code)

    return None


def parse_decklist(path: Path, skip_basics: bool = True) -> Decklist:
    with open(path) as f:
        lines = f.readlines()
    return parse_decklist_string("\n".join(lines), skip_basics=skip_basics)


def parse_decklist_string(content: str, skip_basics: bool = True) -> Decklist:
    entries: list[DeckEntry] = []
    for line in content.splitlines():
        if entry := parse_line(line):
            if skip_basics and is_basic_land(entry.name):
                continue
            entries.append(entry)
    return Decklist(entries=entries)
