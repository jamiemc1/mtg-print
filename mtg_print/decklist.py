import re
from pathlib import Path

from mtg_print.archidekt import (
    extract_deck_name_from_url,
    is_archidekt_url,
)
from mtg_print.archidekt import (
    fetch_decklist as fetch_archidekt_decklist,
)
from mtg_print.basics import is_basic_land
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


def load_decklist(
    source: str, skip_basics: bool = True
) -> tuple[Decklist, Path | None, str | None]:
    """Load decklist from file path or Archidekt URL.

    Returns (decklist, file_path, deck_name_from_url).
    Raises FileNotFoundError for missing files, ArchidektError for URL failures.
    """
    if is_archidekt_url(source):
        decklist = fetch_archidekt_decklist(source, skip_basics=skip_basics)
        return decklist, None, extract_deck_name_from_url(source)
    else:
        decklist_path = Path(source)
        if not decklist_path.exists():
            raise FileNotFoundError(f"File not found: {decklist_path}")
        return parse_decklist(decklist_path, skip_basics=skip_basics), decklist_path, None
