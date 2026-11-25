import contextlib
import io
import runpy
import unittest
from unittest.mock import MagicMock, patch

from scripts import verify_pillow_codecs as guard


class TestVerifyPillowCodecs(unittest.TestCase):
    def test_cli_verifies_real_codecs(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            runpy.run_path(guard.__file__, run_name="__main__")

        self.assertEqual(
            output.getvalue().splitlines(),
            [
                f"{image_format}: encode, decode and thumbnail passed"
                for image_format in ("JPEG", "PNG", "WEBP")
            ],
        )

    def test_missing_jpeg(self):
        with patch.object(guard.features, "check_codec", return_value=False):
            with self.assertRaisesRegex(SystemExit, "Pillow must provide JPEG support"):
                guard.verify_pillow_codecs()

    def test_missing_png(self):
        with patch.object(guard.features, "check_codec", side_effect=[True, False]):
            with self.assertRaisesRegex(SystemExit, "Pillow must provide PNG support"):
                guard.verify_pillow_codecs()

    def test_missing_webp(self):
        with (
            patch.object(guard.features, "check_codec", return_value=True),
            patch.object(guard.features, "check", return_value=False),
        ):
            with self.assertRaisesRegex(SystemExit, "Pillow must provide WebP support"):
                guard.verify_pillow_codecs()

    def test_wrong_decoded_format(self):
        image = MagicMock()
        image.format = "PNG"
        with patch.object(guard.Image, "open") as opened:
            opened.return_value.__enter__.return_value = image
            with self.assertRaisesRegex(SystemExit, "Pillow must preserve JPEG format"):
                guard.verify_pillow_codecs()

    def test_wrong_thumbnail_dimensions(self):
        image = MagicMock()
        image.format = "JPEG"
        image.size = (8, 8)
        with patch.object(guard.Image, "open") as opened:
            opened.return_value.__enter__.return_value = image
            with self.assertRaisesRegex(
                SystemExit, "Pillow must thumbnail JPEG to 8x6"
            ):
                guard.verify_pillow_codecs()
