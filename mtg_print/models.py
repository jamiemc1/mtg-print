from dataclasses import dataclass, field
from datetime import date


@dataclass
class CardFace:
    name: str
    image_uri_png: str
    image_uri_small: str | None = None


@dataclass
class CardPrinting:
    name: str
    set_code: str
    set_name: str
    collector_number: str
    release_date: date
    scryfall_uri: str
    layout: str
    faces: list[CardFace] = field(default_factory=list)

    @property
    def is_double_faced(self) -> bool:
        return self.layout in ("transform", "modal_dfc", "reversible_card")

    @property
    def front_image(self) -> str:
        return self.faces[0].image_uri_png

    @property
    def back_image(self) -> str | None:
        return self.faces[1].image_uri_png if len(self.faces) > 1 else None


@dataclass
class DeckEntry:
    count: int
    name: str
    set_override: str | None = None


@dataclass
class Decklist:
    entries: list[DeckEntry] = field(default_factory=list)

    @property
    def total_cards(self) -> int:
        return sum(e.count for e in self.entries)
