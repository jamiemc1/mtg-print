import time
from datetime import date
from unittest.mock import MagicMock

import pytest

from mtg_print.cache import ImageCache
from mtg_print.models import CardFace, CardPrinting


def make_printing(
    set_code: str = "mh1",
    collector_number: str = "158",
    layout: str = "normal",
    faces: list[CardFace] | None = None,
) -> CardPrinting:
    if faces is None:
        faces = [
            CardFace(
                name="Test Card",
                image_uri_png=f"https://cards.scryfall.io/png/{set_code}/{collector_number}.png",
                image_uri_small=f"https://cards.scryfall.io/small/{set_code}/{collector_number}.jpg",
            )
        ]
    return CardPrinting(
        name="Test Card",
        set_code=set_code,
        set_name="Test Set",
        collector_number=collector_number,
        release_date=date(2020, 1, 1),
        scryfall_uri="https://scryfall.com/card/test/1",
        layout=layout,
        faces=faces,
    )


class TestImageCacheGetPath:
    def test_returns_correct_path_structure(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="mh1", collector_number="158")

        path = cache.get_path(printing)

        assert path == tmp_path / "mh1" / "158.png"

    def test_back_face_has_suffix(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="isd", collector_number="51")

        front_path = cache.get_path(printing, face_index=0)
        back_path = cache.get_path(printing, face_index=1)

        assert front_path == tmp_path / "isd" / "51.png"
        assert back_path == tmp_path / "isd" / "51_back.png"


class TestImageCacheHas:
    def test_returns_false_when_not_cached(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing()

        assert cache.has(printing) is False

    def test_returns_true_when_cached(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="mh1", collector_number="158")

        (tmp_path / "mh1").mkdir()
        (tmp_path / "mh1" / "158.png").write_bytes(b"image data")

        assert cache.has(printing) is True

    def test_checks_correct_face(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="isd", collector_number="51")

        (tmp_path / "isd").mkdir()
        (tmp_path / "isd" / "51.png").write_bytes(b"front")

        assert cache.has(printing, face_index=0) is True
        assert cache.has(printing, face_index=1) is False


class TestImageCacheGetOrDownload:
    def test_returns_cached_file_without_download(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="mh1", collector_number="158")

        (tmp_path / "mh1").mkdir()
        cached_file = tmp_path / "mh1" / "158.png"
        cached_file.write_bytes(b"cached image")

        mock_client = MagicMock()
        result = cache.get_or_download(printing, mock_client)

        assert result == cached_file
        mock_client.download_image.assert_not_called()

    def test_downloads_when_not_cached(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="mh1", collector_number="158")

        mock_client = MagicMock()
        expected_path = tmp_path / "mh1" / "158.png"
        mock_client.download_image.return_value = expected_path

        result = cache.get_or_download(printing, mock_client)

        mock_client.download_image.assert_called_once_with(
            "https://cards.scryfall.io/png/mh1/158.png",
            expected_path,
        )
        assert result == expected_path

    def test_touches_file_on_cache_hit(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing(set_code="mh1", collector_number="158")

        (tmp_path / "mh1").mkdir()
        cached_file = tmp_path / "mh1" / "158.png"
        cached_file.write_bytes(b"cached image")

        old_mtime = cached_file.stat().st_mtime
        time.sleep(0.01)

        mock_client = MagicMock()
        cache.get_or_download(printing, mock_client)

        new_mtime = cached_file.stat().st_mtime
        assert new_mtime > old_mtime

    def test_raises_for_invalid_face_index(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        printing = make_printing()  # Single face

        mock_client = MagicMock()
        with pytest.raises(ValueError, match="No face at index"):
            cache.get_or_download(printing, mock_client, face_index=5)


class TestImageCacheEviction:
    def test_evicts_oldest_files_when_over_limit(self, tmp_path) -> None:
        (tmp_path / "set1").mkdir()
        (tmp_path / "set2").mkdir()

        old_file = tmp_path / "set1" / "old.png"
        new_file = tmp_path / "set2" / "new.png"

        old_file.write_bytes(b"x" * 1000)
        time.sleep(0.01)
        new_file.write_bytes(b"x" * 1000)

        ImageCache(cache_dir=tmp_path, max_size_gb=0.000001)

        assert not old_file.exists()
        assert new_file.exists()

    def test_no_eviction_when_under_limit(self, tmp_path) -> None:
        (tmp_path / "set1").mkdir()
        file1 = tmp_path / "set1" / "card.png"
        file1.write_bytes(b"small file")

        ImageCache(cache_dir=tmp_path, max_size_gb=1.0)

        assert file1.exists()


class TestImageCacheClear:
    def test_removes_all_cached_files(self, tmp_path) -> None:
        (tmp_path / "set1").mkdir()
        (tmp_path / "set2").mkdir()
        (tmp_path / "set1" / "card1.png").write_bytes(b"image1")
        (tmp_path / "set2" / "card2.png").write_bytes(b"image2")

        cache = ImageCache(cache_dir=tmp_path)
        count = cache.clear()

        assert count == 2
        assert not (tmp_path / "set1" / "card1.png").exists()
        assert not (tmp_path / "set2" / "card2.png").exists()

    def test_returns_zero_for_empty_cache(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        count = cache.clear()

        assert count == 0


class TestImageCacheStats:
    def test_returns_file_count_and_size(self, tmp_path) -> None:
        (tmp_path / "set1").mkdir()
        (tmp_path / "set1" / "card1.png").write_bytes(b"x" * 100)
        (tmp_path / "set1" / "card2.png").write_bytes(b"x" * 200)

        cache = ImageCache(cache_dir=tmp_path)
        stats = cache.stats()

        assert stats["file_count"] == 2
        assert stats["total_size_bytes"] == 300

    def test_empty_cache_stats(self, tmp_path) -> None:
        cache = ImageCache(cache_dir=tmp_path)
        stats = cache.stats()

        assert stats["file_count"] == 0
        assert stats["total_size_bytes"] == 0
