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


REQUIRED_DEFAULT_SLOTS = {
    "HEAD", "EYES", "EYEBROWS", "MOUTH", "HAIR_BACK", "HAIR_FRONT",
    "TORSO", "SHIRT", "PANTS", "UPPER_ARM_L", "UPPER_ARM_R",
    "SLEEVE_L", "SLEEVE_R", "FOREARM_L", "FOREARM_R",
    "HAND_L", "HAND_R", "THIGH_L", "THIGH_R", "SHIN_L", "SHIN_R",
    "SHOE_L", "SHOE_R"
}

SLOT_BONES = {
    "HEAD": "head", "EYES": "head", "EYEBROWS": "head", "MOUTH": "head",
    "FACIAL_HAIR": "head", "HAIR_BACK": "head", "HAIR_FRONT": "head",
    "HAT_BACK": "head", "HAT_FRONT": "head",
    "TORSO": "torso", "SHIRT": "torso", "PANTS": "torso",
    "UPPER_ARM_L": "armUL", "SLEEVE_L": "armUL",
    "UPPER_ARM_R": "armUR", "SLEEVE_R": "armUR",
    "FOREARM_L": "foreArmL", "HAND_L": "foreArmL",
    "FOREARM_R": "foreArmR", "HAND_R": "foreArmR",
    "THIGH_L": "thighL", "THIGH_R": "thighR",
    "SHIN_L": "shinL", "SHIN_R": "shinR",
    "SHOE_L": "shinL", "SHOE_R": "shinR"
}


class KenneyPackImporterTests(unittest.TestCase):
    def _fixture(self, root):
        archive = root / "kenney.zip"
        import io
        with zipfile.ZipFile(archive, "w") as zf:
            for name, color in (("head", (220, 80, 50, 255)), ("hand", (80, 120, 220, 255))):
                buffer = io.BytesIO()
                Image.new("RGBA", (16, 24), color).save(buffer, format="PNG")
                zf.writestr(f"Kenney/parts/{name}.png", buffer.getvalue())
        parts = []
        defaults = {}
        for index, (slot, bone) in enumerate((slot, SLOT_BONES[slot]) for slot in sorted(REQUIRED_DEFAULT_SLOTS)):
            part_id = "kenney_" + slot.lower()
            defaults[slot] = part_id
            parts.append({
                "id": part_id,
                "sourceFile": "Kenney/parts/head.png" if bone == "head" else "Kenney/parts/hand.png",
                "slot": slot, "boneId": bone, "pivotX": 0.5, "pivotY": 0.8,
                "widthUnits": 0.18, "heightUnits": 0.20, "zIndex": index
            })
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
            "defaults": defaults, "parts": parts
        }
        map_path = root / "mapping.json"
        map_path.write_text(json.dumps(mapping), encoding="utf-8")
        return archive, map_path, mapping

    def test_imports_pngs_and_emits_manifest_with_shared_rig_and_all_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, mapping, expected = self._fixture(root)
            out = import_kenney_pack(archive, mapping, root / "out")
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["rigId"], "jedl_humanoid_v1")
            self.assertEqual(manifest["rigBones"], sorted(expected["rigBones"]))
            self.assertEqual({p["slot"] for p in manifest["parts"]}, set(SLOT_BONES))
            self.assertEqual(len(manifest["parts"]), len(SLOT_BONES))
            for part in manifest["parts"]:
                self.assertTrue((out / part["file"]).is_file())
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

    def test_rejects_zip_path_traversal_and_noncanonical_slot_bone_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            with zipfile.ZipFile(archive, "a") as zf:
                zf.writestr("../escape.png", b"bad")
            mapping["parts"][0]["sourceFile"] = "../escape.png"
            map_path.write_text(json.dumps(mapping), encoding="utf-8")
            with self.assertRaises(ValueError):
                import_kenney_pack(archive, map_path, root / "out")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive, map_path, mapping = self._fixture(root)
            mapping["parts"][0]["boneId"] = "torso"
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
