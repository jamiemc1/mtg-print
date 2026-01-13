from datetime import date

import httpx
import pytest
from pytest_httpx import HTTPXMock

from mtg_print.scryfall import CardNotFoundError, ScryfallClient

ELVISH_RECLAIMER_RESPONSE = {
    "name": "Elvish Reclaimer",
    "set": "mh1",
    "set_name": "Modern Horizons",
    "collector_number": "158",
    "released_at": "2019-06-14",
    "scryfall_uri": "https://scryfall.com/card/mh1/158",
    "layout": "normal",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/mh1/158.png",
        "small": "https://cards.scryfall.io/small/mh1/158.jpg",
    },
}

DELVER_DFC_RESPONSE = {
    "name": "Delver of Secrets // Insectile Aberration",
    "set": "isd",
    "set_name": "Innistrad",
    "collector_number": "51",
    "released_at": "2011-09-30",
    "scryfall_uri": "https://scryfall.com/card/isd/51",
    "layout": "transform",
    "card_faces": [
        {
            "name": "Delver of Secrets",
            "image_uris": {
                "png": "https://cards.scryfall.io/png/isd/51a.png",
                "small": "https://cards.scryfall.io/small/isd/51a.jpg",
            },
        },
        {
            "name": "Insectile Aberration",
            "image_uris": {
                "png": "https://cards.scryfall.io/png/isd/51b.png",
                "small": "https://cards.scryfall.io/small/isd/51b.jpg",
            },
        },
    ],
}

SEARCH_RESPONSE = {
    "data": [
        ELVISH_RECLAIMER_RESPONSE,
        {
            **ELVISH_RECLAIMER_RESPONSE,
            "set": "mh2",
            "set_name": "Modern Horizons 2",
            "collector_number": "166",
            "released_at": "2021-06-18",
        },
    ]
}


class TestScryfallClientParsePrinting:
    def test_parses_normal_card(self) -> None:
        client = ScryfallClient()
        printing = client._parse_printing(ELVISH_RECLAIMER_RESPONSE)

        assert printing.name == "Elvish Reclaimer"
        assert printing.set_code == "mh1"
        assert printing.set_name == "Modern Horizons"
        assert printing.collector_number == "158"
        assert printing.release_date == date(2019, 6, 14)
        assert printing.layout == "normal"
        assert len(printing.faces) == 1
        assert printing.faces[0].name == "Elvish Reclaimer"
        assert printing.faces[0].image_uri_png == "https://cards.scryfall.io/png/mh1/158.png"

    def test_parses_double_faced_card(self) -> None:
        client = ScryfallClient()
        printing = client._parse_printing(DELVER_DFC_RESPONSE)

        assert printing.name == "Delver of Secrets // Insectile Aberration"
        assert printing.layout == "transform"
        assert printing.is_double_faced is True
        assert len(printing.faces) == 2
        assert printing.faces[0].name == "Delver of Secrets"
        assert printing.faces[1].name == "Insectile Aberration"
        assert printing.front_image == "https://cards.scryfall.io/png/isd/51a.png"
        assert printing.back_image == "https://cards.scryfall.io/png/isd/51b.png"

    def test_normal_card_not_double_faced(self) -> None:
        client = ScryfallClient()
        printing = client._parse_printing(ELVISH_RECLAIMER_RESPONSE)

        assert printing.is_double_faced is False
        assert printing.back_image is None


class TestScryfallClientGetCardByName:
    def test_empty_search_results_raises_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json={"data": []})

        client = ScryfallClient()
        with pytest.raises(CardNotFoundError) as exc_info:
            client.get_card_by_name("Obscure Card")

        assert exc_info.value.card_name == "Obscure Card"

    def test_with_set_code_uses_named_endpoint(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Elvish+Reclaimer&set=mh1",
            json=ELVISH_RECLAIMER_RESPONSE,
        )

        client = ScryfallClient()
        printing = client.get_card_by_name("Elvish Reclaimer", set_code="MH1")

        assert printing.name == "Elvish Reclaimer"
        assert printing.set_code == "mh1"

    def test_without_set_code_uses_search(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/search?q=%21%22Elvish+Reclaimer%22&unique=prints&order=released&dir=asc",
            json=SEARCH_RESPONSE,
        )

        client = ScryfallClient()
        printing = client.get_card_by_name("Elvish Reclaimer")

        assert printing.name == "Elvish Reclaimer"
        assert printing.set_code == "mh1"  # First (oldest) printing

    def test_card_not_found_raises_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Not+A+Real+Card&set=xxx",
            status_code=404,
        )

        client = ScryfallClient()
        with pytest.raises(CardNotFoundError) as exc_info:
            client.get_card_by_name("Not A Real Card", set_code="xxx")

        assert exc_info.value.card_name == "Not A Real Card"
        assert "Card not found" in str(exc_info.value)


class TestScryfallClientSearchPrintings:
    def test_returns_all_printings_oldest_first(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/search?q=%21%22Elvish+Reclaimer%22&unique=prints&order=released&dir=asc",
            json=SEARCH_RESPONSE,
        )

        client = ScryfallClient()
        printings = client.search_printings("Elvish Reclaimer")

        assert len(printings) == 2
        assert printings[0].set_code == "mh1"  # Older
        assert printings[1].set_code == "mh2"  # Newer

    def test_card_not_found_raises_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/search?q=%21%22Fake+Card%22&unique=prints&order=released&dir=asc",
            status_code=404,
        )

        client = ScryfallClient()
        with pytest.raises(CardNotFoundError):
            client.search_printings("Fake Card")


class TestScryfallClientDownloadImage:
    def test_downloads_and_saves_image(self, httpx_mock: HTTPXMock, tmp_path) -> None:
        fake_png_data = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        httpx_mock.add_response(
            url="https://cards.scryfall.io/png/mh1/158.png",
            content=fake_png_data,
        )

        client = ScryfallClient()
        dest = tmp_path / "mh1" / "158.png"
        result = client.download_image("https://cards.scryfall.io/png/mh1/158.png", dest)

        assert result == dest
        assert dest.exists()
        assert dest.read_bytes() == fake_png_data

    def test_creates_parent_directories(self, httpx_mock: HTTPXMock, tmp_path) -> None:
        httpx_mock.add_response(
            url="https://cards.scryfall.io/png/mh1/158.png",
            content=b"image",
        )

        client = ScryfallClient()
        dest = tmp_path / "deep" / "nested" / "path" / "158.png"
        client.download_image("https://cards.scryfall.io/png/mh1/158.png", dest)

        assert dest.exists()


class TestScryfallClientCustomHttpClient:
    def test_accepts_custom_http_client(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(json=ELVISH_RECLAIMER_RESPONSE)

        custom_client = httpx.Client(timeout=60.0)
        client = ScryfallClient(http_client=custom_client)
        printing = client.get_card_by_name("Elvish Reclaimer", set_code="mh1")

        assert printing.name == "Elvish Reclaimer"
