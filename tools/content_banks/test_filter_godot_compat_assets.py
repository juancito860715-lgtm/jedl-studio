import json
import struct
import tempfile
import unittest
from pathlib import Path

from filter_godot_compat_assets import (
    UnsupportedGodotExtensionError,
    filter_catalog,
    inspect_model,
)


def write_glb(path: Path, document: dict) -> None:
    raw = json.dumps(document).encode("utf-8")
    raw += b" " * ((4 - len(raw) % 4) % 4)
    chunk = struct.pack("<II", len(raw), 0x4E4F534A) + raw
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk)


class GodotCompatibilityFilterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets/gallery/3d/extended").mkdir(parents=True)
        (self.root / "assets/gallery").mkdir(exist_ok=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_inspects_required_and_used_extensions(self):
        model = self.root / "model.glb"
        write_glb(model, {
            "asset": {"version": "2.0"},
            "extensionsUsed": ["EXT_meshopt_compression"],
            "extensionsRequired": ["EXT_meshopt_compression", "KHR_mesh_quantization"],
        })
        result = inspect_model(model, "test.model")
        self.assertEqual(
            result["unsupportedGodot441Extensions"],
            ["EXT_meshopt_compression", "KHR_mesh_quantization"],
        )
        self.assertFalse(result["compatibleByExtensionGate"])

    def test_excludes_incompatible_extended_asset_and_records_evidence(self):
        folder = self.root / "assets/gallery/3d/extended/test_asset"
        folder.mkdir()
        model = folder / "model.glb"
        write_glb(model, {
            "asset": {"version": "2.0"},
            "extensionsUsed": ["EXT_meshopt_compression"],
            "extensionsRequired": ["EXT_meshopt_compression"],
        })
        catalog_path = self.root / "assets/gallery/catalog.json"
        catalog_path.write_text(json.dumps({
            "schemaVersion": 2,
            "assets": [{
                "id": "character.test.extended",
                "kind": "3d",
                "path": "res://assets/gallery/3d/extended/test_asset/model.glb",
            }],
        }), encoding="utf-8")
        report = filter_catalog(self.root)
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["assets"], [])
        self.assertFalse(folder.exists())
        self.assertEqual(report["excludedCount"], 1)
        self.assertEqual(report["excludedAssets"][0]["assetId"], "character.test.extended")

    def test_core_model_with_unsupported_extension_fails_closed(self):
        folder = self.root / "assets/gallery/3d/core"
        folder.mkdir(parents=True)
        model = folder / "model.glb"
        write_glb(model, {
            "asset": {"version": "2.0"},
            "extensionsRequired": ["KHR_mesh_quantization"],
        })
        catalog_path = self.root / "assets/gallery/catalog.json"
        catalog_path.write_text(json.dumps({
            "schemaVersion": 2,
            "assets": [{
                "id": "model.core",
                "kind": "3d",
                "path": "res://assets/gallery/3d/core/model.glb",
            }],
        }), encoding="utf-8")
        with self.assertRaises(UnsupportedGodotExtensionError):
            filter_catalog(self.root)

    def test_compatible_model_remains_active(self):
        folder = self.root / "assets/gallery/3d/extended/compatible"
        folder.mkdir()
        model = folder / "model.glb"
        write_glb(model, {"asset": {"version": "2.0"}, "scenes": [{"nodes": []}]})
        catalog_path = self.root / "assets/gallery/catalog.json"
        catalog_path.write_text(json.dumps({
            "schemaVersion": 2,
            "assets": [{
                "id": "model.compatible",
                "kind": "3d",
                "path": "res://assets/gallery/3d/extended/compatible/model.glb",
            }],
        }), encoding="utf-8")
        report = filter_catalog(self.root)
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["assets"]), 1)
        self.assertEqual(report["compatibleCount"], 1)
        self.assertEqual(report["excludedCount"], 0)

    def test_explicit_tevy_policy_excludes_even_an_extension_compatible_source(self):
        folder = self.root / "assets/gallery/3d/extended/tevy"
        folder.mkdir()
        model = folder / "model.glb"
        write_glb(model, {"asset": {"version": "2.0"}, "scenes": [{"nodes": []}]})
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "asset_exclusions.json").write_text(json.dumps({
            "schemaVersion": 1,
            "exclusions": [{
                "assetId": "character.tevy.casual_walker.v1",
                "status": "excluded",
                "reason": "Pending end-to-end validation",
                "activeCatalogAllowed": False,
                "reentryCriteria": ["Import", "Instantiate", "Render"],
            }],
        }), encoding="utf-8")
        catalog_path = self.root / "assets/gallery/catalog.json"
        catalog_path.write_text(json.dumps({
            "schemaVersion": 2,
            "assets": [{
                "id": "character.tevy.casual_walker.v1",
                "kind": "3d",
                "path": "res://assets/gallery/3d/extended/tevy/model.glb",
            }],
        }), encoding="utf-8")
        report = filter_catalog(self.root)
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["assets"], [])
        self.assertFalse(folder.exists())
        self.assertEqual(report["excludedAssets"][0]["status"], "excluded_by_policy")
        self.assertEqual(report["missingExplicitExclusions"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
