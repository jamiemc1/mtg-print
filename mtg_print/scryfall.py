import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from mtg_print.models import CardFace, CardPrinting


class CardNotFoundError(Exception):
    def __init__(self, card_name: str):
        self.card_name = card_name
        super().__init__(f"Card not found: {card_name}")


SCRYFALL_API = "https://api.scryfall.com"
REQUEST_DELAY = 0.1


class ScryfallClient:
    def __init__(self, http_client: httpx.Client | None = None):
        self.client = http_client or httpx.Client(timeout=30.0)
        self.client.headers["User-Agent"] = "MTGPrint/1.0"
        self._last_request: float = 0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request = time.time()

    def _get(
        self, endpoint: str, params: dict[str, str] | None = None, card_name: str | None = None
    ) -> dict[str, Any]:
        self._rate_limit()
        response = self.client.get(f"{SCRYFALL_API}{endpoint}", params=params)
        if response.status_code == 404 and card_name:
            raise CardNotFoundError(card_name)
        response.raise_for_status()
        return response.json()

    def _parse_printing(self, data: dict[str, Any]) -> CardPrinting:
        faces: list[CardFace] = []

        if "card_faces" in data and data.get("layout") in (
            "transform",
            "modal_dfc",
            "reversible_card",
        ):
            for face in data["card_faces"]:
                if "image_uris" in face:
                    faces.append(
                        CardFace(
                            name=face["name"],
                            image_uri_png=face["image_uris"]["png"],
                            image_uri_small=face["image_uris"].get("small"),
                        )
                    )
        elif "image_uris" in data:
            faces.append(
                CardFace(
                    name=data["name"],
                    image_uri_png=data["image_uris"]["png"],
                    image_uri_small=data["image_uris"].get("small"),
                )
            )

        return CardPrinting(
            name=data["name"],
            set_code=data["set"],
            set_name=data["set_name"],
            collector_number=data["collector_number"],
            release_date=date.fromisoformat(data["released_at"]),
            scryfall_uri=data["scryfall_uri"],
            layout=data["layout"],
            faces=faces,
        )

    def get_card_by_name(self, name: str, set_code: str | None = None) -> CardPrinting:
        if set_code:
            params = {"exact": name, "set": set_code.lower()}
            data = self._get("/cards/named", params, card_name=name)
            return self._parse_printing(data)

        printings = self.search_printings(name)
        if not printings:
            raise CardNotFoundError(name)
        return printings[0]

    def search_printings(self, card_name: str) -> list[CardPrinting]:
        params = {"q": f'!"{card_name}"', "unique": "prints", "order": "released", "dir": "asc"}
        data = self._get("/cards/search", params, card_name=card_name)
        return [self._parse_printing(card) for card in data.get("data", [])]

    def download_image(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        response = self.client.get(url)
        response.raise_for_status()
        dest.write_bytes(response.content)
        return dest
