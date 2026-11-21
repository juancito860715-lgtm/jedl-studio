import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asset_pack_pipeline import (
    KENNEY_PACKS,
    SAFE_COMMUNITY_CATEGORIES,
    AssetPackError,
    safe_archive_member,
    validate_cc0_source,
    package_community_assets,
)


class AssetPackPipelineTests(unittest.TestCase):
    def test_catalog_contains_multiple_neutral_asset_categories(self):
        categories = {item["category"] for item in KENNEY_PACKS.values()}
        self.assertTrue({"animals", "characters", "environment", "furniture", "audio"} <= categories)
        self.assertGreaterEqual(len(KENNEY_PACKS), 11)
        for item in KENNEY_PACKS.values():
            self.assertTrue(item["page"].startswith("https://kenney.nl/assets/"))
            self.assertTrue(item["download"].startswith("https://kenney.nl/media/pages/assets/"))
            self.assertIn(item["category"], {"animals", "characters", "environment", "furniture", "audio", "vehicles", "food", "ui"})

    def test_only_reviewed_community_categories_are_included(self):
        self.assertEqual(SAFE_COMMUNITY_CATEGORIES, ("modern-urban", "nature"))

    def test_cc0_source_evidence_is_required(self):
        self.assertTrue(validate_cc0_source("License: CC0 1.0 Universal"))
        with self.assertRaises(AssetPackError):
            validate_cc0_source("License: CC-BY 4.0")
        with self.assertRaises(AssetPackError):
            validate_cc0_source("Free for commercial use")

    def test_rejects_unsafe_archive_paths(self):
        for value in ("../escape.png", "/absolute.png", "a/../../b.png", r"a\\b.png"):
            with self.subTest(value=value), self.assertRaises(AssetPackError):
                safe_archive_member(value)

    def test_accepts_nested_relative_archive_paths(self):
        self.assertEqual(safe_archive_member("nature/trees/oak.png"), "nature/trees/oak.png")

    def test_packages_only_community_folders_with_cc0_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            output = root / "out" / "community.zip"
            for category, pack in (("nature", "trees"), ("modern-urban", "town")):
                folder = source / category / pack
                folder.mkdir(parents=True)
                (folder / "SOURCE.md").write_text("License: CC0 1.0\n", encoding="utf-8")
                (folder / "asset.txt").write_text("licensed content", encoding="utf-8")
            result = package_community_assets(source, output)
            self.assertEqual(result["packCount"], 2)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("nature/trees/SOURCE.md", names)
                self.assertIn("modern-urban/town/SOURCE.md", names)
                self.assertNotIn("sci-fi/", "\n".join(names))

    def test_rejects_community_pack_without_cc0_source_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "source" / "nature" / "trees"
            folder.mkdir(parents=True)
            (folder / "SOURCE.md").write_text("License: unknown", encoding="utf-8")
            with self.assertRaises(AssetPackError):
                package_community_assets(root / "source", root / "out.zip")


if __name__ == "__main__":
    unittest.main()
