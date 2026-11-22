import json
import tempfile
import unittest
from pathlib import Path

from verify_godot_import_artifacts import verify_import_artifacts


class GodotImportArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "assets/gallery/2d/background.jpg"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(b"jpeg-test-data")
        self.imported = self.root / ".godot/imported/background.jpg-abc.ctex"
        self.imported.parent.mkdir(parents=True)
        self.imported.write_bytes(b"imported-texture")
        (self.root / "assets/gallery/manifest.json").write_text(json.dumps({
            "files": [{"path": "res://assets/gallery/2d/background.jpg", "sizeBytes": 14, "sha256": "unused"}]
        }), encoding="utf-8")
        (Path(str(self.source) + ".import")).write_text(
            'path="res://.godot/imported/background.jpg-abc.ctex"\n',
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_accepts_source_sidecar_and_nonempty_cache(self):
        result = verify_import_artifacts(self.root)
        self.assertEqual(result["expectedImportableResources"], 1)
        self.assertEqual(result["verifiedSidecarsAndCache"], 1)

    def test_rejects_missing_import_sidecar(self):
        Path(str(self.source) + ".import").unlink()
        with self.assertRaisesRegex(ValueError, "missing .import sidecars"):
            verify_import_artifacts(self.root)

    def test_rejects_missing_imported_cache_file(self):
        self.imported.unlink()
        with self.assertRaisesRegex(ValueError, "missing .godot/imported cache outputs"):
            verify_import_artifacts(self.root)

    def test_rejects_empty_manifest_inventory(self):
        (self.root / "assets/gallery/manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no file inventory"):
            verify_import_artifacts(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
