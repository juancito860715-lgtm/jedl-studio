import json
import struct
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

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

        self.element = self.root / "assets/gallery/2d/cutout.png"
        cutout = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        ImageDraw.Draw(cutout).rectangle((24, 24, 104, 104), fill=(220, 80, 40, 255))
        cutout.save(self.element, "PNG")

        self.background = self.root / "assets/gallery/2d/background.jpg"
        Image.new("RGB", (1024, 512), (20, 80, 40)).save(self.background, "JPEG")

        self.model = self.root / "assets/gallery/3d/model.glb"
        make_glb(self.model)
        self.catalog_path = self.root / "assets/gallery/catalog.json"
        self.manifest_path = self.root / "assets/gallery/manifest.json"
        self.catalog = {
            "schemaVersion": 2,
            "assets": [
                {"id": "element.test", "kind": "2d", "category": "Elementos 2D individuales",
                 "path": "res://assets/gallery/2d/cutout.png", "preview_path": "res://assets/gallery/2d/cutout.png",
                 "license": "CC0-1.0", "licenseEvidence": "https://polyhaven.com/license",
                 "source": "https://polyhaven.com/a/test", "sha256": sha256(self.element),
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
        files = []
        for item in self.catalog["assets"]:
            source_path = self.root / item["path"][6:]
            item["sizeBytes"] = source_path.stat().st_size if source_path.is_file() else -1
            assets.append({"assetId": item["id"], "path": item["path"], "sha256": item["sha256"],
                           "sizeBytes": item["sizeBytes"], "dependencies": [], "license": item["license"]})
            if source_path.is_file():
                files.append({"path": item["path"], "sizeBytes": source_path.stat().st_size,
                              "sha256": sha256(source_path)})
        self.catalog_path.write_text(json.dumps(self.catalog), encoding="utf-8")
        files.append({"path": "res://assets/gallery/catalog.json",
                      "sizeBytes": self.catalog_path.stat().st_size, "sha256": sha256(self.catalog_path)})
        self.manifest_path.write_text(json.dumps({
            "schemaVersion": 1, "catalogSha256": sha256(self.catalog_path),
            "assets": assets, "files": files
        }), encoding="utf-8")

    def test_accepts_transparent_2d_cutout_and_glb_without_photographic_backgrounds(self):
        result = validate_assets(self.root)
        self.assertEqual(result["photographic_backgrounds"], 0)
        self.assertEqual(result["elements_2d"], 1)
        self.assertEqual(result["models_3d"], 1)
        self.assertEqual(result["files"], 3)

    def test_rejects_photographic_backgrounds(self):
        self.catalog["assets"][0]["path"] = "res://assets/gallery/2d/background.jpg"
        self.catalog["assets"][0]["preview_path"] = "res://assets/gallery/2d/background.jpg"
        self.catalog["assets"][0]["category"] = "Fondos fotográficos"
        self.catalog["assets"][0]["sha256"] = sha256(self.background)
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "2D elements must be transparent cutouts"):
            validate_assets(self.root)

    def test_rejects_nontransparent_2d_assets(self):
        Image.new("RGB", (128, 128), (220, 80, 40)).save(self.element, "PNG")
        self.catalog["assets"][0]["sha256"] = sha256(self.element)
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "must contain alpha transparency"):
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
        self.model.with_suffix(".gltf").write_text(json.dumps(document), encoding="utf-8")
        self.catalog["assets"][1]["path"] = "res://assets/gallery/3d/model.gltf"
        self.catalog["assets"][1]["sha256"] = sha256(self.model.with_suffix(".gltf"))
        self.write_catalog_and_manifest()
        with self.assertRaisesRegex(ValueError, "External network URI"):
            validate_assets(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
