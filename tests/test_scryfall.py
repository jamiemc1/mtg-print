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
            url="https://api.scryfall.com/cards/search?q=%21%22Elvish+Reclaimer%22+include%3Aextras&unique=prints&order=released&dir=asc",
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
            url="https://api.scryfall.com/cards/search?q=%21%22Elvish+Reclaimer%22+include%3Aextras&unique=prints&order=released&dir=asc",
            json=SEARCH_RESPONSE,
        )

        client = ScryfallClient()
        printings = client.search_printings("Elvish Reclaimer")

        assert len(printings) == 2
        assert printings[0].set_code == "mh1"  # Older
        assert printings[1].set_code == "mh2"  # Newer

    def test_card_not_found_raises_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/search?q=%21%22Fake+Card%22+include%3Aextras&unique=prints&order=released&dir=asc",
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


AVENGER_RESPONSE = {
    "name": "Avenger of Zendikar",
    "set": "c18",
    "set_name": "Commander 2018",
    "collector_number": "129",
    "released_at": "2018-08-10",
    "scryfall_uri": "https://scryfall.com/card/c18/129",
    "layout": "normal",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/c18/129.png",
        "small": "https://cards.scryfall.io/small/c18/129.jpg",
    },
    "all_parts": [
        {
            "object": "related_card",
            "id": "abc123",
            "component": "combo_piece",
            "name": "Avenger of Zendikar",
            "uri": "https://api.scryfall.com/cards/abc123",
        },
        {
            "object": "related_card",
            "id": "plant123",
            "component": "token",
            "name": "Plant",
            "uri": "https://api.scryfall.com/cards/plant123",
        },
    ],
}

PLANT_TOKEN_RESPONSE = {
    "name": "Plant",
    "set": "tc18",
    "set_name": "Commander 2018 Tokens",
    "collector_number": "1",
    "released_at": "2018-08-10",
    "scryfall_uri": "https://scryfall.com/card/tc18/1",
    "layout": "token",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/tc18/1.png",
        "small": "https://cards.scryfall.io/small/tc18/1.jpg",
    },
}

TEFERI_RESPONSE = {
    "name": "Teferi, Hero of Dominaria",
    "set": "dom",
    "set_name": "Dominaria",
    "collector_number": "207",
    "released_at": "2018-04-27",
    "scryfall_uri": "https://scryfall.com/card/dom/207",
    "layout": "normal",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/dom/207.png",
        "small": "https://cards.scryfall.io/small/dom/207.jpg",
    },
    "all_parts": [
        {
            "object": "related_card",
            "id": "emblem123",
            "component": "combo_piece",
            "name": "Teferi, Hero of Dominaria Emblem",
            "uri": "https://api.scryfall.com/cards/emblem123",
        },
        {
            "object": "related_card",
            "id": "teferi123",
            "component": "combo_piece",
            "name": "Teferi, Hero of Dominaria",
            "uri": "https://api.scryfall.com/cards/teferi123",
        },
    ],
}

TEFERI_EMBLEM_RESPONSE = {
    "name": "Teferi, Hero of Dominaria Emblem",
    "set": "tdom",
    "set_name": "Dominaria Tokens",
    "collector_number": "1",
    "released_at": "2018-04-27",
    "scryfall_uri": "https://scryfall.com/card/tdom/1",
    "layout": "emblem",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/tdom/1.png",
        "small": "https://cards.scryfall.io/small/tdom/1.jpg",
    },
}

GISELA_RESPONSE = {
    "name": "Gisela, the Broken Blade",
    "set": "emn",
    "set_name": "Eldritch Moon",
    "collector_number": "28",
    "released_at": "2016-07-22",
    "scryfall_uri": "https://scryfall.com/card/emn/28",
    "layout": "meld",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/emn/28.png",
        "small": "https://cards.scryfall.io/small/emn/28.jpg",
    },
    "all_parts": [
        {
            "object": "related_card",
            "id": "checklist123",
            "component": "token",
            "name": "Eldritch Moon Checklist",
            "uri": "https://api.scryfall.com/cards/checklist123",
        },
        {
            "object": "related_card",
            "id": "brisela123",
            "component": "meld_result",
            "name": "Brisela, Voice of Nightmares",
            "uri": "https://api.scryfall.com/cards/brisela123",
        },
        {
            "object": "related_card",
            "id": "gisela123",
            "component": "meld_part",
            "name": "Gisela, the Broken Blade",
            "uri": "https://api.scryfall.com/cards/gisela123",
        },
    ],
}

BRISELA_RESPONSE = {
    "name": "Brisela, Voice of Nightmares",
    "set": "emn",
    "set_name": "Eldritch Moon",
    "collector_number": "15b",
    "released_at": "2016-07-22",
    "scryfall_uri": "https://scryfall.com/card/emn/15b",
    "layout": "meld",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/emn/15b.png",
        "small": "https://cards.scryfall.io/small/emn/15b.jpg",
    },
}

NO_PARTS_RESPONSE = {
    **ELVISH_RECLAIMER_RESPONSE,
}

MINSC_RESPONSE = {
    "name": "Minsc & Boo, Timeless Heroes",
    "set": "clb",
    "set_name": "Commander Legends: Battle for Baldur's Gate",
    "collector_number": "285",
    "released_at": "2022-06-10",
    "scryfall_uri": "https://scryfall.com/card/clb/285",
    "layout": "normal",
    "image_uris": {
        "png": "https://cards.scryfall.io/png/clb/285.png",
        "small": "https://cards.scryfall.io/small/clb/285.jpg",
    },
    "all_parts": [
        {
            "object": "related_card",
            "id": "minsc123",
            "component": "combo_piece",
            "name": "Minsc & Boo, Timeless Heroes",
            "uri": "https://api.scryfall.com/cards/minsc123",
        },
        {
            "object": "related_card",
            "id": "boo123",
            "component": "token",
            "name": "Boo",
            "uri": "https://api.scryfall.com/cards/boo123",
        },
        {
            "object": "related_card",
            "id": "aminsc123",
            "component": "combo_piece",
            "name": "A-Minsc & Boo, Timeless Heroes",
            "uri": "https://api.scryfall.com/cards/aminsc123",
        },
    ],
}

BOO_TOKEN_RESPONSE = {
    "name": "Boo",
    "set": "tclb",
    "set_name": "Commander Legends: Battle for Baldur's Gate Tokens",
    "collector_number": "1",
    "released_at": "2022-06-10",
    "scryfall_uri": "https://scryfall.com/card/tclb/1",
    "layout": "token",
    "digital": False,
    "image_uris": {
        "png": "https://cards.scryfall.io/png/tclb/1.png",
        "small": "https://cards.scryfall.io/small/tclb/1.jpg",
    },
}

ALCHEMY_MINSC_RESPONSE = {
    "name": "A-Minsc & Boo, Timeless Heroes",
    "set": "hbg",
    "set_name": "Alchemy Horizons: Baldur's Gate",
    "collector_number": "285",
    "released_at": "2022-07-07",
    "scryfall_uri": "https://scryfall.com/card/hbg/285",
    "layout": "normal",
    "digital": True,
    "image_uris": {
        "png": "https://cards.scryfall.io/png/hbg/285.png",
        "small": "https://cards.scryfall.io/small/hbg/285.jpg",
    },
}


class TestScryfallClientGetRelatedParts:
    def test_returns_tokens_for_card(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Avenger+of+Zendikar",
            json=AVENGER_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/plant123",
            json=PLANT_TOKEN_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Avenger of Zendikar")

        assert len(parts) == 1
        assert parts[0].name == "Plant"
        assert parts[0].layout == "token"

    def test_returns_emblems_for_planeswalker(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Teferi%2C+Hero+of+Dominaria",
            json=TEFERI_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/emblem123",
            json=TEFERI_EMBLEM_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Teferi, Hero of Dominaria")

        assert len(parts) == 1
        assert parts[0].name == "Teferi, Hero of Dominaria Emblem"
        assert parts[0].layout == "emblem"

    def test_excludes_self_reference(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Teferi%2C+Hero+of+Dominaria",
            json=TEFERI_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/emblem123",
            json=TEFERI_EMBLEM_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Teferi, Hero of Dominaria")

        part_names = [p.name for p in parts]
        assert "Teferi, Hero of Dominaria" not in part_names

    def test_excludes_checklist_cards(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Gisela%2C+the+Broken+Blade",
            json=GISELA_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/brisela123",
            json=BRISELA_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Gisela, the Broken Blade")

        part_names = [p.name for p in parts]
        assert "Eldritch Moon Checklist" not in part_names
        assert "Brisela, Voice of Nightmares" in part_names

    def test_returns_empty_for_card_without_parts(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Elvish+Reclaimer",
            json=NO_PARTS_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Elvish Reclaimer")

        assert parts == []

    def test_with_set_code(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Avenger+of+Zendikar&set=c18",
            json=AVENGER_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/plant123",
            json=PLANT_TOKEN_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Avenger of Zendikar", set_code="C18")

        assert len(parts) == 1
        assert parts[0].name == "Plant"

    def test_excludes_digital_only_cards(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Minsc+%26+Boo%2C+Timeless+Heroes",
            json=MINSC_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/boo123",
            json=BOO_TOKEN_RESPONSE,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/aminsc123",
            json=ALCHEMY_MINSC_RESPONSE,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Minsc & Boo, Timeless Heroes")

        part_names = [p.name for p in parts]
        assert "Boo" in part_names
        assert "A-Minsc & Boo, Timeless Heroes" not in part_names
        assert len(parts) == 1

    def test_excludes_normal_cards_from_related_parts(self, httpx_mock: HTTPXMock) -> None:
        elk_response = {
            "name": "Elk",
            "set": "tecl",
            "set_name": "Throne of Eldraine Tokens",
            "collector_number": "1",
            "released_at": "2019-10-04",
            "scryfall_uri": "https://scryfall.com/card/tecl/1",
            "layout": "token",
            "image_uris": {
                "png": "https://cards.scryfall.io/png/tecl/1.png",
                "small": "https://cards.scryfall.io/small/tecl/1.jpg",
            },
            "all_parts": [
                {
                    "object": "related_card",
                    "id": "elk123",
                    "component": "token",
                    "name": "Elk",
                    "uri": "https://api.scryfall.com/cards/elk123",
                },
                {
                    "object": "related_card",
                    "id": "oko123",
                    "component": "combo_piece",
                    "name": "Oko, Thief of Crowns",
                    "uri": "https://api.scryfall.com/cards/oko123",
                },
            ],
        }
        oko_response = {
            "name": "Oko, Thief of Crowns",
            "set": "eld",
            "set_name": "Throne of Eldraine",
            "collector_number": "197",
            "released_at": "2019-10-04",
            "scryfall_uri": "https://scryfall.com/card/eld/197",
            "layout": "normal",
            "image_uris": {
                "png": "https://cards.scryfall.io/png/eld/197.png",
                "small": "https://cards.scryfall.io/small/eld/197.jpg",
            },
        }
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/named?exact=Elk",
            json=elk_response,
        )
        httpx_mock.add_response(
            url="https://api.scryfall.com/cards/oko123",
            json=oko_response,
        )

        client = ScryfallClient()
        parts = client.get_related_parts("Elk")

        part_names = [p.name for p in parts]
        assert "Oko, Thief of Crowns" not in part_names
        assert len(parts) == 0
