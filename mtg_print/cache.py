import shutil
import sys
from pathlib import Path

from mtg_print.models import CardPrinting
from mtg_print.scryfall import ScryfallClient

DEFAULT_CACHE_DIR = Path.home() / ".mtg_print" / "cache"
DEFAULT_MAX_CACHE_SIZE_GB = 2.0


class ImageCache:
    def __init__(
        self,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        max_size_gb: float = DEFAULT_MAX_CACHE_SIZE_GB,
    ):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_gb = max_size_gb
        self._evict_if_needed()

    def get_path(self, printing: CardPrinting, face_index: int = 0) -> Path:
        suffix = "" if face_index == 0 else "_back"
        return self.cache_dir / printing.set_code / f"{printing.collector_number}{suffix}.png"

    def has(self, printing: CardPrinting, face_index: int = 0) -> bool:
        return self.get_path(printing, face_index).exists()

    def _evict_if_needed(self) -> int:
        max_bytes = self.max_size_gb * (1024**3)
        files = list(self.cache_dir.rglob("*.png"))
        total_size = sum(f.stat().st_size for f in files)

        if total_size <= max_bytes:
            return 0

        files_by_mtime = sorted(files, key=lambda f: f.stat().st_mtime)
        evicted = 0

        while total_size > max_bytes and files_by_mtime:
            oldest = files_by_mtime.pop(0)
            total_size -= oldest.stat().st_size
            oldest.unlink()
            evicted += 1

        if evicted > 0:
            print(
                f"Cache exceeded {self.max_size_gb} GB, evicted {evicted} old images",
                file=sys.stderr,
            )

        return evicted

    def get_or_download(
        self, printing: CardPrinting, client: ScryfallClient, face_index: int = 0
    ) -> Path:
        path = self.get_path(printing, face_index)
        if path.exists():
            path.touch()
            return path

        if face_index < len(printing.faces):
            url = printing.faces[face_index].image_uri_png
            return client.download_image(url, path)

        raise ValueError(f"No face at index {face_index} for {printing.name}")

    def clear(self) -> int:
        count = len(list(self.cache_dir.rglob("*.png")))
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        return count

    def stats(self) -> dict[str, int]:
        files = list(self.cache_dir.rglob("*.png"))
        total_size = sum(f.stat().st_size for f in files)
        return {"file_count": len(files), "total_size_bytes": total_size}
