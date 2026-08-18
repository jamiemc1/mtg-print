import hashlib
import json
import logging
import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from mtg_print.models import CardFace, CardPrinting

logger = logging.getLogger(__name__)


class CardNotFoundError(Exception):
    def __init__(self, card_name: str):
        self.card_name = card_name
        super().__init__(f"Card not found: {card_name}")


SCRYFALL_API = "https://api.scryfall.com"
REQUEST_DELAY = 0.1
MAX_RETRIES = 3
API_CACHE_TTL_SECONDS = 86400
API_CACHE_DIR = Path.home() / ".mtg_print" / "api_cache"


class ScryfallClient:
    def __init__(
        self,
        http_client: httpx.Client | None = None,
        api_cache_dir: Path | None = API_CACHE_DIR,
    ):
        self.client = http_client or httpx.Client(timeout=30.0)
        self.client.headers["User-Agent"] = "MTGPrint/1.0"
        self._last_request: float = 0
        self._api_cache_dir = api_cache_dir
        if self._api_cache_dir:
            self._api_cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, endpoint: str, params: dict[str, str] | None) -> Path | None:
        if not self._api_cache_dir:
            return None
        raw = endpoint + json.dumps(params, sort_keys=True, default=str)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self._api_cache_dir / f"{digest}.json"

    def _read_cache(self, cache_path: Path | None) -> dict[str, Any] | None:
        if not cache_path or not cache_path.exists():
            return None
        age = time.time() - cache_path.stat().st_mtime
        if age > API_CACHE_TTL_SECONDS:
            cache_path.unlink()
            return None
        return json.loads(cache_path.read_text())

    def _write_cache(self, cache_path: Path | None, data: dict[str, Any]) -> None:
        if not cache_path:
            return
        cache_path.write_text(json.dumps(data))

    def clear_api_cache(self) -> int:
        if not self._api_cache_dir:
            return 0
        files = list(self._api_cache_dir.glob("*.json"))
        for f in files:
            f.unlink()
        return len(files)

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)
        self._last_request = time.time()

    def _get(
        self, endpoint: str, params: dict[str, str] | None = None, card_name: str | None = None
    ) -> dict[str, Any]:
        cache_path = self._cache_key(endpoint, params)
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached
        for attempt in range(MAX_RETRIES):
            self._rate_limit()
            response = self.client.get(f"{SCRYFALL_API}{endpoint}", params=params)

            if response.status_code != 429:
                break

            retry_after = response.headers.get("Retry-After")
            if retry_after is None:
                response.raise_for_status()
            delay = int(retry_after)
            logger.debug(
                f"Rate limited on {endpoint}, waiting {delay} s"
                f" (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(delay)
        else:
            response.raise_for_status()

        if response.status_code == 404 and card_name:
            raise CardNotFoundError(card_name)
        response.raise_for_status()
        data = response.json()
        self._write_cache(cache_path, data)
        return data

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
            legalities=data.get("legalities", {}),
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
        params = {
            "q": f'!"{card_name}" include:extras',
            "unique": "prints",
            "order": "released",
            "dir": "asc",
        }
        data = self._get("/cards/search", params, card_name=card_name)
        printings = [self._parse_printing(card) for card in data.get("data", [])]
        # Filter out art series and other layouts without printable images
        return [p for p in printings if p.faces]

    def fetch_bytes(self, url: str) -> bytes:
        self._rate_limit()
        response = self.client.get(url)
        response.raise_for_status()
        return response.content

    def download_image(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self.fetch_bytes(url))
        return dest

    def get_related_parts(self, name: str, set_code: str | None = None) -> list[CardPrinting]:
        # Scryfall layout types: https://scryfall.com/docs/api/layouts
        extra_layouts = {"token", "emblem", "meld"}

        if set_code:
            params = {"exact": name, "set": set_code.lower()}
        else:
            params = {"exact": name}
        data = self._get("/cards/named", params, card_name=name)

        parts: list[CardPrinting] = []
        for part in data.get("all_parts", []):
            part_name = part.get("name", "")
            if part_name == name:
                continue
            if "Checklist" in part_name:
                continue
            part_data = self._get(part["uri"].replace(SCRYFALL_API, ""))
            if part_data.get("digital", False):
                continue
            if part_data.get("layout") not in extra_layouts:
                continue
            parts.append(self._parse_printing(part_data))
        return parts
