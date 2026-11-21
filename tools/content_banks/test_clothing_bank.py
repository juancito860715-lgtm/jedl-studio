import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

from generate_clothing_bank import build

class ClothingBankTests(unittest.TestCase):
    def test_generates_six_original_cc0_wardrobe_pngs_with_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"bank"
            manifest=build(root)
            self.assertEqual("jedl_original_clothing_v1",manifest["id"])
            self.assertEqual("CC0-1.0",manifest["license"])
            self.assertTrue(manifest["commercialUse"] and manifest["apkRedistributionAllowed"])
            self.assertEqual(6,manifest["assetCount"])
            for item in manifest["assets"]:
                path=root/item["file"]
                self.assertTrue(path.is_file())
                raw=path.read_bytes()
                self.assertEqual(item["sha256"],hashlib.sha256(raw).hexdigest())
                with Image.open(path) as image:
                    self.assertEqual((128,128),image.size)
                    self.assertEqual("RGBA",image.mode)
                self.assertEqual("Clothing",item["category"])

if __name__=="__main__": unittest.main()
