import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from build_style_packs import build_style_packs

class StylePackBuildTest(unittest.TestCase):
    def test_builds_default_and_grayscale_boceto_with_same_rig_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            pngs = source / "png"
            pngs.mkdir()
            parts = []
            for index in range(42):
                part_id = f"part_{index}"
                parts.append({
                    "id": part_id, "slot": "HEAD", "boneId": "head",
                    "file": f"png/{part_id}.png", "pivotX": 0.5, "pivotY": 0.5,
                    "widthUnits": 0.2, "heightUnits": 0.3, "zIndex": index,
                    "offsetX": 0.0, "offsetY": 0.0
                })
                Image.new("RGBA", (8, 8), (220, 30, 40, 255)).save(pngs / f"{part_id}.png")
            manifest = {"id": "test", "version": 1, "rigId": "jedl_humanoid_v1",\n                        "rigBones": ["torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",\n                                     "thighL", "shinL", "thighR", "shinR"],\n                        "parts": parts, "defaults": {"HEAD": "part_0"}}
            manifest_path = source / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = build_style_packs(manifest_path, pngs, root / "styles")
            default = json.loads((output / "default" / "manifest.json").read_text())
            sketch = json.loads((output / "boceto" / "manifest.json").read_text())
            self.assertEqual(len(default["parts"]), 42)
            self.assertEqual(len(sketch["parts"]), 42)
            for original, gray in zip(default["parts"], sketch["parts"]):
                self.assertEqual({k:v for k,v in original.items() if k != "file"},
                                 {k:v for k,v in gray.items() if k != "file"})
                self.assertEqual(original["boneId"], gray["boneId"])
                self.assertEqual(original["pivotX"], gray["pivotX"])
                self.assertEqual(original["pivotY"], gray["pivotY"])
                self.assertEqual(original["zIndex"], gray["zIndex"])
                self.assertTrue((output / "default" / original["file"]).is_file())
                self.assertTrue((output / "boceto" / gray["file"]).is_file())
            with Image.open(output / "default" / "characters" / "part_0.png") as color:
                self.assertNotEqual(color.getpixel((0,0))[0], color.getpixel((0,0))[1])
            with Image.open(output / "boceto" / "characters" / "part_0.png") as gray:
                r,g,b,a = gray.getpixel((0,0))
                self.assertEqual(r,g); self.assertEqual(g,b); self.assertEqual(a,255)

    def test_rejects_missing_or_duplicate_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps({"parts": [], "defaults": {}}))
            with self.assertRaises(ValueError):
                build_style_packs(manifest_path, root, root / "styles")

if __name__ == "__main__":
    unittest.main()
