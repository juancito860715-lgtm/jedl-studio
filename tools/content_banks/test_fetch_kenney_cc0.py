import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fetch_kenney_cc0 import _safe_member, resolve_download, PACKS


class KenneyContentBankTests(unittest.TestCase):
    def test_only_explicit_cc0_environment_packs_are_catalogued(self):
        self.assertEqual(set(PACKS), {"objects", "foliage", "roguelike", "urban"})
        for spec in PACKS.values():
            self.assertIn("kenney.nl/assets/", spec["page"])
            self.assertIn("object", spec["kind"])
            self.assertEqual(len(spec["sha256"]), 64)
            self.assertTrue(spec["archive"].endswith(".zip"))

    def test_resolves_only_https_kenney_download_links(self):
        page = b"""
        <html><body>
          <a href="/assets/tiny-town/download">Download</a>
          <a href="https://example.org/other.zip">Untrusted</a>
          <a href="http://kenney.nl/files/bad.zip">Insecure</a>
        </body></html>
        """
        self.assertEqual(
            resolve_download("https://kenney.nl/assets/tiny-town", page),
            "https://kenney.nl/assets/tiny-town/download"
        )

    def test_rejects_external_or_missing_download_links(self):
        with self.assertRaises(ValueError):
            resolve_download("https://kenney.nl/assets/tiny-town",
                             b'<a href="https://example.org/pack.zip">download</a>')

    def test_rejects_zip_path_traversal_and_windows_paths(self):
        for path in ("../escape.png", "/absolute.png", "folder/../../escape.png",
                     r"folder\\escape.png"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                _safe_member(path)

    def test_accepts_nested_relative_paths(self):
        self.assertEqual(_safe_member("Tiles/Tree.png"), "Tiles/Tree.png")


if __name__ == "__main__":
    unittest.main()
