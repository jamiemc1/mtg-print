import base64
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def imgcat_available() -> bool:
    return shutil.which("imgcat") is not None


def display_image_iterm(image_data: bytes, width: int = 20) -> None:
    b64 = base64.b64encode(image_data).decode("ascii")
    sys.stdout.write(f"\033]1337;File=inline=1;width={width}:{b64}\a")
    sys.stdout.write("\n")
    sys.stdout.flush()


def display_image_imgcat(image_path: Path, width: int = 20) -> None:
    subprocess.run(["imgcat", "-W", f"{width}", str(image_path)], check=False)


def display_image(image_data: bytes, width: int = 20) -> bool:
    if imgcat_available():
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_data)
            tmp_path = Path(f.name)
        try:
            display_image_imgcat(tmp_path, width)
            return True
        finally:
            tmp_path.unlink(missing_ok=True)

    try:
        display_image_iterm(image_data, width)
        return True
    except Exception:
        return False
