"""Unit tests for config and path management."""

import os
import tempfile
import unittest
from datetime import datetime

from revendik.config import AppConfig, PathManager, get_today_date_fr


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.paths = PathManager(base_dir=self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_ensure_dirs_creates_required_directories(self) -> None:
        for key in ("images", "gabarits", "signatures", "sauvegardes", "exports_griefs", "exports_retraits"):
            path = self.paths.get_path(key)
            self.assertTrue(os.path.isdir(path), f"Directory {key} should exist")

    def test_app_config_load_save(self) -> None:
        cfg_file = os.path.join(self.temp_dir.name, "config", "config.json")
        cfg = AppConfig(
            etablissement_defaut="Hôpital Enfant-Jésus",
            signature_defaut="Jean_Tremblay",
        )
        cfg.save(cfg_file)

        loaded = AppConfig.load(cfg_file)
        self.assertEqual(loaded.etablissement_defaut, "Hôpital Enfant-Jésus")
        self.assertEqual(loaded.signature_defaut, "Jean_Tremblay")

    def test_get_today_date_fr(self) -> None:
        dt = datetime(2026, 10, 15)
        formatted = get_today_date_fr(dt)
        self.assertEqual(formatted, "15 octobre 2026")


if __name__ == "__main__":
    unittest.main()
