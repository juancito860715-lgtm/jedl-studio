import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

from build_root_manifest import build_manifest


def make_glb(path: Path) -> None:
    document = json.dumps({"asset": {"version": "2.0"}, "scenes": [{"nodes": []}]}).encode("utf-8")
    document += b" " * ((4 - len(document) % 4) % 4)
    chunk = struct.pack("<II", len(document), 0x4E4F534A) + document
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk)


class RootManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets/gallery/2d").mkdir(parents=True)
        (self.root / "assets/characters").mkdir(parents=True)
        (self.root / "assets/gallery/2d/background.jpg").write_bytes(b"background-bytes")
        make_glb(self.root / "assets/characters/Fox.glb")
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

    def test_builds_root_manifest_with_asset_ids_hashes_sizes_and_empty_embedded_dependencies(self):
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
        fox_path = self.root / "assets/characters/Fox.glb"
        self.assertEqual(fox["sha256"], hashlib.sha256(fox_path.read_bytes()).hexdigest())
        self.assertEqual(fox["sizeBytes"], fox_path.stat().st_size)
        self.assertEqual(fox["dependencies"], [])
        saved_catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_catalog["assets"][1]["sha256"], fox["sha256"])
        self.assertEqual(saved_catalog["assets"][1]["sizeBytes"], fox["sizeBytes"])
        self.assertTrue((self.root / "assets/gallery/manifest.json").is_file())

    def test_records_external_gltf_image_dependencies(self):
        textures = self.root / "assets/characters/textures"
        textures.mkdir()
        dependency = textures / "skin.png"
        dependency.write_bytes(b"texture-dependency")
        model = self.root / "assets/characters/Walker.gltf"
        model.write_text(json.dumps({
            "asset": {"version": "2.0"},
            "images": [{"uri": "textures/skin.png"}],
        }), encoding="utf-8")
        self.catalog["assets"][1]["path"] = "res://assets/characters/Walker.gltf"
        self.catalog["assets"][1]["preview_path"] = "res://assets/characters/textures/skin.png"
        self._write_catalog()
        manifest = build_manifest(self.root)
        character = next(item for item in manifest["assets"] if item["assetId"] == "character.fox")
        self.assertEqual(character["dependencies"], ["res://assets/characters/textures/skin.png"])
        self.assertIn(
            "res://assets/characters/textures/skin.png",
            {item["path"] for item in manifest["files"]},
        )

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

    def test_rejects_license_not_in_catalog_policy(self):
        self.catalog["assets"][0]["license"] = "UNKNOWN-LICENSE"
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "License is not allowed"):
            build_manifest(self.root)

    def test_rejects_declared_sha256_mismatch(self):
        self.catalog["assets"][0]["sha256"] = "0" * 64
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            build_manifest(self.root)

    def test_rejects_declared_size_mismatch(self):
        self.catalog["assets"][0]["sizeBytes"] = 999
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "File size mismatch"):
            build_manifest(self.root)

    def test_rejects_assets_without_offline_or_license_evidence(self):
        self.catalog["assets"][0]["offline"] = False
        self._write_catalog()
        with self.assertRaisesRegex(ValueError, "offline and placeable"):
            build_manifest(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
