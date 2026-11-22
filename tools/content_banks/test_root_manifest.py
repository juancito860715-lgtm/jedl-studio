import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_root_manifest import build_manifest


class RootManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets/gallery/2d").mkdir(parents=True)
        (self.root / "assets/characters").mkdir(parents=True)
        (self.root / "assets/gallery/2d/background.jpg").write_bytes(b"background-bytes")
        (self.root / "assets/characters/Fox.glb").write_bytes(b"fox-bytes")
        (self.root / "assets/characters/Fox.LICENSE.md").write_text("CC0-1.0\n", encoding="utf-8")
        self.catalog_path = self.root / "assets/gallery/catalog.json"
        self.catalog = {
            "schemaVersion": 2,
            "catalogId": "test_catalog_v1",
            "licensePolicy": {"allowed": ["CC0-1.0"]},
            "assets": [
                {
                    "id": "background.test",
                    "path": "res://assets/gallery/2d/background.jpg",
                    "preview_path": "res://assets/gallery/2d/background.jpg",
                    "kind": "2d",
                    "category": "backgrounds",
                    "license": "CC0-1.0",
                    "offline": True,
                    "placeable": True,
                },
                {
                    "id": "character.fox",
                    "path": "res://assets/characters/Fox.glb",
                    "kind": "3d",
                    "category": "characters",
                    "license": "CC0-1.0",
                    "offline": True,
                    "placeable": True,
                },
            ],
        }
        self._write_catalog()

    def tearDown(self):
        self.temp.cleanup()

    def _write_catalog(self):
        self.catalog_path.write_text(json.dumps(self.catalog, indent=2), encoding="utf-8")

    def test_builds_root_manifest_with_asset_ids_and_sha256(self):
        manifest = build_manifest(self.root)
        self.assertEqual(manifest["assetCount"], 2)
        self.assertGreaterEqual(manifest["fileCount"], 4)
        self.assertEqual(
            {item["assetId"] for item in manifest["assets"]},
            {"background.test", "character.fox"},
        )
        self.assertEqual(
            manifest["catalogSha256"],
            hashlib.sha256(self.catalog_path.read_bytes()).hexdigest(),
        )
        fox = next(item for item in manifest["assets"] if item["assetId"] == "character.fox")
        self.assertEqual(fox["sha256"], hashlib.sha256(b"fox-bytes").hexdigest())
        saved_catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_catalog["assets"][1]["sha256"], fox["sha256"])
        self.assertTrue((self.root / "assets/gallery/manifest.json").is_file())

    def test_rejects_duplicate_asset_ids(self):
        self.catalog["assets"].append(dict(self.catalog["assets"][0]))
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "Duplicate asset id"):
            build_manifest(self.root)

    def test_rejects_path_traversal(self):
        self.catalog["assets"][0]["path"] = "res://assets/gallery/2d/../../outside.jpg"
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "Unsafe asset path"):
            build_manifest(self.root)

    def test_rejects_missing_files(self):
        self.catalog["assets"][0]["path"] = "res://assets/gallery/2d/missing.jpg"
        self._write_catalog()
        with self.assertRaises(FileNotFoundError):
            build_manifest(self.root)

    def test_rejects_assets_without_offline_or_license_evidence(self):
        self.catalog["assets"][0]["offline"] = False
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "offline and placeable"):
            build_manifest(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
