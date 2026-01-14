import io

import pytest
from PIL import Image

from mtg_print.terminal import composite_images_horizontal


def make_test_image(width: int = 100, height: int = 140, color: tuple = (255, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    output = io.BytesIO()
    img.save(output, format="JPEG")
    return output.getvalue()


class TestCompositeImagesHorizontal:
    def test_returns_bytes(self) -> None:
        images = [make_test_image()]

        result = composite_images_horizontal(images)

        assert isinstance(result, bytes)

    def test_output_is_valid_jpeg(self) -> None:
        images = [make_test_image(), make_test_image()]

        result = composite_images_horizontal(images)

        img = Image.open(io.BytesIO(result))
        assert img.format == "JPEG"

    def test_single_image_preserves_dimensions_with_label_space(self) -> None:
        images = [make_test_image(width=100, height=140)]

        result = composite_images_horizontal(images)

        img = Image.open(io.BytesIO(result))
        assert img.width == 100
        assert img.height == 140 + 20  # label_height = 20

    def test_two_images_side_by_side(self) -> None:
        images = [make_test_image(width=100, height=140), make_test_image(width=100, height=140)]

        result = composite_images_horizontal(images, spacing_px=10)

        img = Image.open(io.BytesIO(result))
        assert img.width == 100 + 10 + 100  # img + spacing + img
        assert img.height == 140 + 20  # single row + label

    def test_respects_max_per_row(self) -> None:
        images = [make_test_image(width=50, height=70) for _ in range(4)]

        result = composite_images_horizontal(images, spacing_px=10, max_per_row=2)

        img = Image.open(io.BytesIO(result))
        expected_width = 50 + 10 + 50  # 2 images per row
        expected_height = (70 + 20) * 2 + 10  # 2 rows + spacing between rows
        assert img.width == expected_width
        assert img.height == expected_height

    def test_six_images_in_two_rows(self) -> None:
        images = [make_test_image(width=50, height=70) for _ in range(6)]

        result = composite_images_horizontal(images, spacing_px=10, max_per_row=3)

        img = Image.open(io.BytesIO(result))
        expected_width = 50 + 10 + 50 + 10 + 50  # 3 images per row
        expected_height = (70 + 20) + 10 + (70 + 20)  # 2 rows + spacing
        assert img.width == expected_width
        assert img.height == expected_height

    def test_raises_for_empty_list(self) -> None:
        with pytest.raises(ValueError, match="No images"):
            composite_images_horizontal([])

    def test_index_labels_are_drawn(self) -> None:
        images = [make_test_image(color=(0, 0, 0)) for _ in range(3)]

        result = composite_images_horizontal(images, spacing_px=10)

        img = Image.open(io.BytesIO(result))
        label_area = img.crop((0, 140, 100, 160))
        pixels = list(label_area.tobytes())
        has_white = any(p > 200 for p in pixels)
        assert has_white  # Some white pixels from the label text


class TestCompositeImagesSpacing:
    def test_zero_spacing(self) -> None:
        images = [make_test_image(width=50, height=70), make_test_image(width=50, height=70)]

        result = composite_images_horizontal(images, spacing_px=0)

        img = Image.open(io.BytesIO(result))
        assert img.width == 100  # No spacing

    def test_large_spacing(self) -> None:
        images = [make_test_image(width=50, height=70), make_test_image(width=50, height=70)]

        result = composite_images_horizontal(images, spacing_px=50)

        img = Image.open(io.BytesIO(result))
        assert img.width == 150  # 50 + 50 + 50
