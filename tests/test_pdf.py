"""Unit tests for PDF generator and browser detection."""

import unittest
from revendik.pdf import find_browser, detect_browser_info, PDFGenerator


class TestPDF(unittest.TestCase):
    def test_browser_detection(self) -> None:
        browser = find_browser()
        found, info = detect_browser_info()
        self.assertEqual(bool(browser), found)
        if found:
            self.assertIn("(", info)

    def test_pdf_generator_instance(self) -> None:
        gen = PDFGenerator()
        if gen.browser_path:
            self.assertTrue(bool(gen.ensure_browser()))


if __name__ == "__main__":
    unittest.main()
