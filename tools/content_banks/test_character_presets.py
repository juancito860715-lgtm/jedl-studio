import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "content_banks"))
import build_character_presets


class CharacterPresetBuildTests(unittest.TestCase):
    def test_generates_rig_compatible_reusable_presets(self):
        presets = build_character_presets.build()
        manifest = json.loads(build_character_presets.OUTPUT.read_text(encoding="utf-8"))
        source = json.loads(build_character_presets.SOURCE.read_text(encoding="utf-8"))
        by_id = {part["id"]: part for part in source["parts"]}
        self.assertEqual(len(presets), 8)
        self.assertEqual(manifest["presetCount"], 8)
        for preset in presets:
            self.assertTrue(set(source["defaults"]).issubset(set(preset["selectedParts"])))
            for slot, part_id in preset["selectedParts"].items():
                self.assertEqual(by_id[part_id]["slot"], slot)

    def test_contains_multiple_hair_and_expression_choices(self):
        presets = build_character_presets.build()
        self.assertEqual({p["id"] for p in presets}, {
            "master_default", "hair_spiky", "hair_curly", "expression_happy",
            "expression_surprised", "urban_cap", "cap_brim", "expression_serious"
        })


if __name__ == "__main__":
    unittest.main()
