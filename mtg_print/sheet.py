from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

CARD_WIDTH_MM = 63.5
CARD_HEIGHT_MM = 88.9
GUIDE_LENGTH_MM = 3


class SheetGenerator:
    def __init__(
        self,
        page_size: tuple[float, float] = A4,
        cards_per_row: int = 3,
        rows_per_page: int = 3,
        margin_mm: float = 10,
        guides: bool = False,
    ):
        self.page_size = page_size
        self.cards_per_row = cards_per_row
        self.rows_per_page = rows_per_page
        self.margin_mm = margin_mm
        self.cards_per_page = cards_per_row * rows_per_page
        self.guides = guides

    def _draw_corner_guides(
        self,
        pdf_canvas: canvas.Canvas,
        card_x: float,
        card_y: float,
        card_width: float,
        card_height: float,
    ) -> None:
        guide_length = GUIDE_LENGTH_MM * mm
        pdf_canvas.setStrokeColorRGB(0, 0, 0)
        pdf_canvas.setLineWidth(0.5)

        corners = [
            (card_x, card_y + card_height),
            (card_x + card_width, card_y + card_height),
            (card_x + card_width, card_y),
            (card_x, card_y),
        ]
        line_directions = [
            ((-1, 0), (0, 1)),
            ((1, 0), (0, 1)),
            ((1, 0), (0, -1)),
            ((-1, 0), (0, -1)),
        ]

        for (corner_x, corner_y), (horizontal_dir, vertical_dir) in zip(corners, line_directions):
            pdf_canvas.line(
                corner_x,
                corner_y,
                corner_x + horizontal_dir[0] * guide_length,
                corner_y + horizontal_dir[1] * guide_length,
            )
            pdf_canvas.line(
                corner_x,
                corner_y,
                corner_x + vertical_dir[0] * guide_length,
                corner_y + vertical_dir[1] * guide_length,
            )

    def generate(
        self,
        card_images: list[Path],
        output_path: Path,
    ) -> None:
        pdf_canvas = canvas.Canvas(str(output_path), pagesize=self.page_size)
        pdf_canvas.setViewerPreference("Duplex", "/Simplex")
        pdf_canvas.setViewerPreference("PrintScaling", "/None")
        page_width, page_height = self.page_size

        card_width = CARD_WIDTH_MM * mm
        card_height = CARD_HEIGHT_MM * mm

        total_cards_width = self.cards_per_row * card_width
        total_cards_height = self.rows_per_page * card_height
        x_offset = (page_width - total_cards_width) / 2
        y_offset = (page_height - total_cards_height) / 2

        for index, image_path in enumerate(card_images):
            if index > 0 and index % self.cards_per_page == 0:
                pdf_canvas.showPage()

            position_on_page = index % self.cards_per_page
            column = position_on_page % self.cards_per_row
            row = position_on_page // self.cards_per_row

            card_x = x_offset + column * card_width
            card_y = page_height - y_offset - (row + 1) * card_height

            pdf_canvas.drawImage(
                str(image_path),
                card_x,
                card_y,
                width=card_width,
                height=card_height,
                preserveAspectRatio=True,
            )

            if self.guides:
                self._draw_corner_guides(pdf_canvas, card_x, card_y, card_width, card_height)

        pdf_canvas.save()
