import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from import_kenney_pack import import_kenney_pack


class KenneyPackImporterTests(unittest.TestCase):
    def _fixture(self, root):
        archive = root / "kenney.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            import io
            buffer = io.BytesIO()
            Image.new("RGBA", (16, 24), (220, 80, 50, 255)).save(buffer, format="PNG")
            zf.writestr("Kenney/parts/head.png", buffer.getvalue())
            zf.writestr("Kenney/parts/hand.png", buffer.getvalue())
        mapping = {
            "id": "kenney_modular_character_pack",
            "title": "Kenney Modular Character Pack",
            "source": "https://opengameart.org/content/modular-character-pack",
            "license": "CC0-1.0",
            "licenseEvidence": "https://opengameart.org/content/modular-character-pack",
            "licenseTerms": "https://creativecommons.org/publicdomain/zero/1.0/",
            "rigId": "jedl_humanoid_v1",
            "rigBones": ["torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",
                         "thighL", "shinL", "thighR", "shinR"],
            "defaults": {"HEAD": "kenney_head", "HAND_L": "kenney_hand"},
            "parts": [
                {"id": "kenney_head", "sourceFile": "Kenney/parts/head.png", "slot": "HEAD",
                 "boneId": "head", "pivotX": 0.5, "pivotY": 0.8, "widthUnits": 0.18,
                 "heightUnits": 0.20, "zIndex": 10},
                {"id": "kenney_hand", "sourceFile": "Kenney/parts/hand.png", "slot": "HAND_L",
                 "boneId": "foreArmL", "pivotX": 0.5, "pivotY": 0.1, "widthUnits": 0.06,
                 "heightUnits": 0.05, "zIndex": 20}
            ]
        }
        map_path = root / "mapping.json"
        map_path.write_text(json.dumps(mapping), encoding="utf-8")
        return archive, map_path, mapping

    def test_imports_pngs_and_emits_manifest_with_shared_rig(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, mapping, expected = self._fixture(root)
            out = import_kenney_pack(archive, mapping, root / "out")
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["rigId"], "jedl_humanoid_v1")
            self.assertEqual(manifest["rigBones"], expected["rigBones"])
            self.assertEqual({p["id"] for p in manifest["parts"]},
                             {"kenney_head", "kenney_hand"})
            for part in manifest["parts"]:
                self.assertTrue((out / part["file"]).is_file())
                self.assertTrue((out / part["file"]).is_relative_to(out))
            self.assertTrue((out / "LICENSE.txt").is_file())
            self.assertTrue((out / "SOURCE.json").is_file())

    def test_rejects_non_commercial_or_unverified_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            mapping["license"] = "CC-BY-NC-4.0"
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_kenney_pack(archive, map_path, root / "out")

    def test_rejects_zip_path_traversal_and_non_png_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            with zipfile.ZipFile(archive, "a") as zf:
                zf.writestr("../escape.png", b"bad")
            mapping["parts"][0]["sourceFile"] = "../escape.png"
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_kenney_pack(archive, map_path, root / "out")

    def test_rejects_missing_bones_and_duplicate_part_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            mapping["rigBones"].remove("head")
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_kenney_pack(archive, map_path, root / "out")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            mapping["parts"][1]["id"] = mapping["parts"][0]["id"]
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_kenney_pack(archive, map_path, root / "out")


if __name__ == "__main__":
    unittest.main()
