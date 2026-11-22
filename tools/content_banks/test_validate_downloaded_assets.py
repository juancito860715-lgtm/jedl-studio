import json
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from validate_downloaded_assets import validate_assets, sha256


def make_glb(path: Path) -> None:
    document = json.dumps({"asset": {"version": "2.0"}, "scenes": [{"nodes": []}]}).encode("utf-8")
    document += b" " * ((4 - len(document) % 4) % 4)
    chunk = struct.pack("<II", len(document), 0x4E4F534A) + document
    payload = struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk
    path.write_bytes(payload)


class DownloadedAssetsValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets/gallery/2d").mkdir(parents=True)
        (self.root / "assets/gallery/3d").mkdir(parents=True)
        (self.root / "assets/characters").mkdir(parents=True)
        self.background = self.root / "assets/gallery/2d/bg.jpg"
        Image.new("RGB", (1024, 512), (20, 80, 40)).save(self.background, "JPEG")
        self.model = self.root / "assets/gallery/3d/model.glb"
        make_glb(self.model)
        self.catalog_path = self.root / "assets/gallery/catalog.json"
        self.manifest_path = self.root / "assets/gallery/manifest.json"
        self.catalog = {
            "schemaVersion": 2,
            "assets": [
                {"id": "background.test", "kind": "2d", "category": "Fondos fotográficos",
                 "path": "res://assets/gallery/2d/bg.jpg", "preview_path": "res://assets/gallery/2d/bg.jpg",
                 "license": "CC0-1.0", "licenseEvidence": "https://polyhaven.com/license",
                 "source": "https://polyhaven.com/a/test", "sha256": sha256(self.background),
                 "offline": True, "placeable": True},
                {"id": "model.test", "kind": "3d", "category": "Props",
                 "path": "res://assets/gallery/3d/model.glb", "license": "CC0-1.0",
                 "licenseEvidence": "https://polyhaven.com/license", "source": "https://polyhaven.com/a/test",
                 "sha256": sha256(self.model), "offline": True, "placeable": True}
            ]
        }
        self.write_catalog_and_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def write_catalog_and_manifest(self):
        self.catalog_path.write_text(json.dumps(self.catalog), encoding="utf-8")
        assets = []
        for item in self.catalog["assets"]:
            assets.append({"assetId": item["id"], "path": item["path"], "sha256": item["sha256"],
                           "license": item["license"]})
        files = []
        for path in (self.background, self.model, self.catalog_path):
            files.append({"path": "res://" + path.relative_to(self.root).as_posix(),
                          "sizeBytes": path.stat().st_size, "sha256": sha256(path)})
        self.manifest_path.write_text(json.dumps({
            "schemaVersion": 1, "catalogSha256": sha256(self.catalog_path),
            "assets": assets, "files": files
        }), encoding="utf-8")

    def test_accepts_valid_photographic_background_and_glb_with_verified_hashes(self):
        result = validate_assets(self.root)
        self.assertEqual(result["photographic_backgrounds"], 1)
        self.assertEqual(result["models_3d"], 1)
        self.assertEqual(result["files"], 3)

    def test_rejects_png_2d_elements(self):
        self.catalog["assets"][0]["path"] = "res://assets/gallery/2d/bg.png"
        self.write_catalog_and_manifest()
        with self.assertRaises((ValueError, FileNotFoundError)):
            validate_assets(self.root)

    def test_rejects_unapproved_license(self):
        self.catalog["assets"][0]["license"] = "UNKNOWN"
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "License is not approved"):
            validate_assets(self.root)

    def test_rejects_corrupt_model_hash(self):
        self.catalog["assets"][1]["sha256"] = "0" * 64
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            validate_assets(self.root)

    def test_rejects_bad_glb_header(self):
        self.model.write_bytes(b"not-a-glb-file")
        self.catalog["assets"][1]["sha256"] = sha256(self.model)
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "GLB is truncated"):
            validate_assets(self.root)

    def test_rejects_external_network_dependencies(self):
        document = {"asset": {"version": "2.0"}, "buffers": [{"uri": "https://example.com/data.bin"}]}
        encoded = json.dumps(document).encode("utf-8")
        self.model.with_suffix(".gltf").write_text(json.dumps(document), encoding="utf-8")
        self.catalog["assets"][1]["path"] = "res://assets/gallery/3d/model.gltf"
        self.catalog["assets"][1]["sha256"] = sha256(self.model.with_suffix(".gltf"))
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "External network URI"):
            validate_assets(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
