from unittest.mock import MagicMock, patch

from reportlab.lib.pagesizes import A4

from mtg_print.sheet import CARD_HEIGHT_MM, CARD_WIDTH_MM, GUIDE_LENGTH_MM, SheetGenerator


class TestSheetGeneratorDefaults:
    def test_default_page_size_is_a4_portrait(self):
        generator = SheetGenerator()
        assert generator.page_size == A4

    def test_default_grid_is_3x3(self):
        generator = SheetGenerator()
        assert generator.cards_per_row == 3
        assert generator.rows_per_page == 3

    def test_default_cards_per_page(self):
        generator = SheetGenerator()
        assert generator.cards_per_page == 9

    def test_default_guides_disabled(self):
        generator = SheetGenerator()
        assert generator.guides is False

    def test_custom_guides_enabled(self):
        generator = SheetGenerator(guides=True)
        assert generator.guides is True


class TestSheetGeneratorConstants:
    def test_card_width_is_standard_mtg(self):
        assert CARD_WIDTH_MM == 63.5

    def test_card_height_is_standard_mtg(self):
        assert CARD_HEIGHT_MM == 88.9

    def test_guide_length(self):
        assert GUIDE_LENGTH_MM == 3


class TestSheetGeneratorViewerPreferences:
    @patch("mtg_print.sheet.canvas.Canvas")
    def test_sets_duplex_simplex(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        generator = SheetGenerator()
        generator.generate([], tmp_path / "output.pdf")

        mock_canvas.setViewerPreference.assert_any_call("Duplex", "/Simplex")

    @patch("mtg_print.sheet.canvas.Canvas")
    def test_sets_print_scaling_none(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        generator = SheetGenerator()
        generator.generate([], tmp_path / "output.pdf")

        mock_canvas.setViewerPreference.assert_any_call("PrintScaling", "/None")


class TestSheetGeneratorGuides:
    @patch("mtg_print.sheet.canvas.Canvas")
    def test_guides_not_drawn_when_disabled(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        image_path = tmp_path / "card.png"
        image_path.write_bytes(b"fake image")

        generator = SheetGenerator(guides=False)
        generator.generate([image_path], tmp_path / "output.pdf")

        mock_canvas.line.assert_not_called()

    @patch("mtg_print.sheet.canvas.Canvas")
    def test_guides_drawn_when_enabled(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        image_path = tmp_path / "card.png"
        image_path.write_bytes(b"fake image")

        generator = SheetGenerator(guides=True)
        generator.generate([image_path], tmp_path / "output.pdf")

        assert mock_canvas.line.called

    @patch("mtg_print.sheet.canvas.Canvas")
    def test_guides_draw_eight_lines_per_card(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        image_path = tmp_path / "card.png"
        image_path.write_bytes(b"fake image")

        generator = SheetGenerator(guides=True)
        generator.generate([image_path], tmp_path / "output.pdf")

        assert mock_canvas.line.call_count == 8

    @patch("mtg_print.sheet.canvas.Canvas")
    def test_guides_set_stroke_color_black(self, mock_canvas_class, tmp_path):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        image_path = tmp_path / "card.png"
        image_path.write_bytes(b"fake image")

        generator = SheetGenerator(guides=True)
        generator.generate([image_path], tmp_path / "output.pdf")

        mock_canvas.setStrokeColorRGB.assert_called_with(0, 0, 0)
