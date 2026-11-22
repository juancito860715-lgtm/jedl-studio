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


    def test_accepts_platform_specific_path_variants(self):
        variants = [
            ('path.s3tc', 'background.jpg-abc.s3tc.ctex'),
            ('path.etc2', 'background.jpg-abc.etc2.ctex'),
            ('path.bptc', 'background.jpg-abc.bptc.ctex'),
        ]
        for key, filename in variants:
            with self.subTest(key=key):
                cache = self.root / ".godot/imported" / filename
                cache.write_bytes(b"valid-import-output")
                Path(str(self.source) + ".import").write_text(
                    f'{key}="res://.godot/imported/{filename}"\\n', encoding="utf-8"
                )
                result = verify_import_artifacts(self.root)
                self.assertEqual(result["verifiedSidecarsAndCache"], 1)
    def test_accepts_dest_files_array_variant(self):
        cache = self.root / ".godot/imported/background-dest.ctex"
        cache.write_bytes(b"valid-import-output")
        Path(str(self.source) + ".import").write_text(
            '[deps]\\ndest_files=["res://.godot/imported/background-dest.ctex"]\\n',
            encoding="utf-8",
        )
        result = verify_import_artifacts(self.root)
        self.assertEqual(result["verifiedSidecarsAndCache"], 1)

    def test_rejects_cache_path_outside_imported_directory(self):
        outside = self.root / "outside.ctex"
        outside.write_bytes(b"not-an-import-cache")
        Path(str(self.source) + ".import").write_text(
            'path="res://outside.ctex"\\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "missing .godot/imported cache outputs"):
            verify_import_artifacts(self.root)

    def test_rejects_empty_cache_output(self):
        self.imported.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "missing .godot/imported cache outputs"):
            verify_import_artifacts(self.root)

    def test_rejects_empty_manifest_inventory(self):
        (self.root / "assets/gallery/manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no file inventory"):
            verify_import_artifacts(self.root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
