import json
import sys
import unittest
from PIL import Image
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as avatar_build

class AvatarBankBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = avatar_build.build()
        cls.output = HERE / "out"

    def test_exactly_forty_unique_png_parts_are_generated(self):
        self.assertEqual(len(self.manifest["parts"]), 42)
        ids = [part["id"] for part in self.manifest["parts"]]
        self.assertEqual(len(ids), len(set(ids)))
        pngs = list((self.output / "png").glob("*.png"))
        self.assertEqual(len(pngs), 42)


    def test_body_pngs_contain_filled_silhouettes_and_transparent_exterior(self):
        body_parts = (
            "head_skin", "torso_skin", "shirt_tee_torso", "pants_jeans_waist",
            "armU_skin_L", "armU_skin_R", "thigh_jeans_L", "thigh_jeans_R",
        )
        by_id = {part["id"]: part for part in self.manifest["parts"]}
        for part_id in body_parts:
            with self.subTest(part=part_id):
                image = Image.open(self.output / by_id[part_id]["file"]).convert("RGBA")
                pixels = list(image.getdata())
                filled = sum(1 for r, g, b, a in pixels if a >= 240 and r >= 245 and g >= 245 and b >= 245)
                inked = sum(1 for r, g, b, a in pixels if a >= 240 and r <= 35 and g <= 35 and b <= 35)
                transparent = sum(1 for _, _, _, a in pixels if a == 0)
                self.assertGreater(filled, 20, f"{part_id} has no solid raster fill")
                self.assertGreater(inked, 0, f"{part_id} has no preserved ink outline")
                self.assertGreater(transparent, 0, f"{part_id} lost transparent exterior")

    def test_both_upper_arms_and_shirt_sleeves_are_generated_and_defaulted(self):
        by_id = {part["id"]: part for part in self.manifest["parts"]}
        expected = {
            "armU_skin_L": ("UPPER_ARM_L", "armUL"),
            "armU_skin_R": ("UPPER_ARM_R", "armUR"),
            "shirt_tee_sleeve_L": ("SLEEVE_L", "armUL"),
            "shirt_tee_sleeve_R": ("SLEEVE_R", "armUR"),
        }
        for part_id, (slot, bone) in expected.items():
            with self.subTest(part=part_id):
                self.assertIn(part_id, by_id)
                part = by_id[part_id]
                self.assertEqual(part["slot"], slot)
                self.assertEqual(part["boneId"], bone)
                self.assertEqual(self.manifest["defaults"][slot], part_id)
                image_path = self.output / part["file"]
                self.assertTrue(image_path.is_file())
                with Image.open(image_path) as image:
                    self.assertEqual(image.mode, "RGBA")
                    self.assertIsNotNone(image.getchannel("A").getbbox())

    def test_manifest_slots_match_real_kotlin_enum(self):
        allowed = {
            "HEAD", "EAR_L", "EAR_R", "EYES", "EYEBROWS", "NOSE", "MOUTH",
            "FACIAL_HAIR", "HAIR_BACK", "HAIR_FRONT", "HAT_BACK", "HAT_FRONT",
            "NECK", "TORSO", "SHIRT", "PANTS", "UPPER_ARM_L", "UPPER_ARM_R",
            "SLEEVE_L", "SLEEVE_R", "FOREARM_L", "FOREARM_R", "HAND_L", "HAND_R",
            "THIGH_L", "THIGH_R", "SHIN_L", "SHIN_R", "FOOT_L", "FOOT_R",
            "SHOE_L", "SHOE_R", "GLASSES", "CHAIN", "MEDAL", "WATCH",
            "STICK_L", "STICK_R", "DRUM", "DRUM_HEAD", "DRUM_STAND"
        }
        self.assertTrue({p["slot"] for p in self.manifest["parts"]} <= allowed)
        by_id = {p["id"]: p for p in self.manifest["parts"]}
        for slot, part_id in self.manifest["defaults"].items():
            self.assertIn(slot, allowed)
            self.assertEqual(by_id[part_id]["slot"], slot)

    def test_every_png_path_pivot_and_bone_is_valid(self):
        for part in self.manifest["parts"]:
            with self.subTest(part=part["id"]):
                path = self.output / part["file"]
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)
                self.assertGreater(part["widthUnits"], 0)
                self.assertGreater(part["heightUnits"], 0)
                self.assertGreaterEqual(part["pivotX"], 0)
                self.assertLessEqual(part["pivotX"], 1)
                self.assertGreaterEqual(part["pivotY"], 0)
                self.assertLessEqual(part["pivotY"], 1)
                self.assertIn(part["boneId"], avatar_build.SUPPORTED_BONES)

if __name__ == "__main__":
    unittest.main()
