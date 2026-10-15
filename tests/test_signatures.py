"""Unit tests for signatures repository and canvas math."""

import os
import tempfile
import unittest
from PIL import Image

from revendik.config import PathManager
from revendik.signatures import SignatureManager, coords_to_css, css_to_coords, sanitize_sig_filename


class TestSignatures(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.paths = PathManager(base_dir=self.temp_dir.name)
        self.sig_manager = SignatureManager(self.paths)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sanitize_sig_filename(self) -> None:
        self.assertEqual(sanitize_sig_filename("Jean Tremblay"), "jean_tremblay")
        self.assertEqual(sanitize_sig_filename("Élise L'Heureux"), "élise_lheureux")

    def test_coordinate_conversion_roundtrip(self) -> None:
        x_orig, y_orig = 50.0, 120.0
        orig_w = 200.0
        scale = 0.5

        css_l, css_b, css_w = coords_to_css(x_orig, y_orig, orig_w, scale)
        x_calc, y_calc = css_to_coords(css_l, css_b)

        self.assertAlmostEqual(x_orig, x_calc, delta=0.1)
        self.assertAlmostEqual(y_orig, y_calc, delta=0.1)

    def test_save_load_delete_signature(self) -> None:
        img = Image.new("RGBA", (100, 50), color="blue")
        sig = self.sig_manager.save_signature(
            name="Test Delegue",
            image=img,
            x=15.0,
            y=140.0,
            scale=0.8,
        )
        self.assertEqual(sig.nom, "Test Delegue")

        # Verify listing
        names = self.sig_manager.list_signatures()
        self.assertIn("Test Delegue", names)

        # Verify retrieval
        loaded = self.sig_manager.get_signature("Test Delegue")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.nom, "Test Delegue")

        # Verify image path
        img_path = self.sig_manager.get_image_path(loaded)
        self.assertTrue(os.path.exists(img_path))

        # Verify delete
        deleted = self.sig_manager.delete_signature("Test Delegue")
        self.assertTrue(deleted)
        self.assertNotIn("Test Delegue", self.sig_manager.list_signatures())
        self.assertFalse(os.path.exists(img_path))


if __name__ == "__main__":
    unittest.main()
