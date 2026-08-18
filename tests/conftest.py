from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def isolated_api_cache(tmp_path):
    cache_dir = tmp_path / "api_cache"
    with patch("mtg_print.scryfall.ScryfallClient.__init__.__defaults__", (None, cache_dir)):
        yield cache_dir
