from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9


class SheetGenerator:
    def __init__(
        self,
        page_size: tuple[float, float] = landscape(A4),
        cards_per_row: int = 4,
        rows_per_page: int = 2,
        margin_mm: float = 10,
    ):
        self.page_size = page_size
        self.cards_per_row = cards_per_row
        self.rows_per_page = rows_per_page
        self.margin_mm = margin_mm
        self.cards_per_page = cards_per_row * rows_per_page

    def generate(
        self,
        card_images: list[Path],
        output_path: Path,
    ) -> None:
        c = canvas.Canvas(str(output_path), pagesize=self.page_size)
        page_width, page_height = self.page_size

        card_width = CARD_WIDTH_MM * mm
        card_height = CARD_HEIGHT_MM * mm

        total_cards_width = self.cards_per_row * card_width
        total_cards_height = self.rows_per_page * card_height
        x_offset = (page_width - total_cards_width) / 2
        y_offset = (page_height - total_cards_height) / 2

        for i, image_path in enumerate(card_images):
            if i > 0 and i % self.cards_per_page == 0:
                c.showPage()

            position_on_page = i % self.cards_per_page
            col = position_on_page % self.cards_per_row
            row = position_on_page // self.cards_per_row

            x = x_offset + col * card_width
            y = page_height - y_offset - (row + 1) * card_height

            c.drawImage(
                str(image_path),
                x,
                y,
                width=card_width,
                height=card_height,
                preserveAspectRatio=True,
            )

        c.save()
