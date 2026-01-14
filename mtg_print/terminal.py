import base64
import io
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont


def get_terminal_width() -> int:
    return shutil.get_terminal_size().columns


def display_image_iterm(image_data: bytes, width: int = 20) -> None:
    b64 = base64.b64encode(image_data).decode("ascii")
    sys.stdout.write(f"\033]1337;File=inline=1;width={width}:{b64}\a\n")
    sys.stdout.flush()


def display_image(image_data: bytes, width: int = 20) -> bool:
    try:
        display_image_iterm(image_data, width)
        return True
    except Exception:
        return False


def composite_images_horizontal(
    images: list[bytes], spacing_px: int = 10, max_per_row: int = 6
) -> bytes:
    pil_images = [Image.open(io.BytesIO(data)) for data in images]
    if not pil_images:
        raise ValueError("No images to composite")

    label_height = 20
    img_width = pil_images[0].width
    img_height = pil_images[0].height

    num_rows = (len(pil_images) + max_per_row - 1) // max_per_row
    images_in_widest_row = min(len(pil_images), max_per_row)

    total_width = images_in_widest_row * img_width + spacing_px * (images_in_widest_row - 1)
    total_height = num_rows * (img_height + label_height) + spacing_px * (num_rows - 1)

    composite = Image.new("RGB", (total_width, total_height), color=(30, 30, 30))
    draw = ImageDraw.Draw(composite)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        font = ImageFont.load_default()

    for i, img in enumerate(pil_images):
        row = i // max_per_row
        col = i % max_per_row

        x = col * (img_width + spacing_px)
        y = row * (img_height + label_height + spacing_px)

        composite.paste(img, (x, y))

        label = str(i + 1)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = x + (img_width - text_width) // 2
        text_y = y + img_height + 2
        draw.text((text_x, text_y), label, fill=(255, 255, 255), font=font)

    output = io.BytesIO()
    composite.save(output, format="JPEG", quality=85)
    return output.getvalue()


def display_images_horizontal(images: list[bytes], spacing_px: int = 10) -> bool:
    if not images:
        return True

    try:
        composite_data = composite_images_horizontal(images, spacing_px)
        terminal_width = get_terminal_width()
        return display_image(composite_data, width=terminal_width)
    except Exception:
        return False
