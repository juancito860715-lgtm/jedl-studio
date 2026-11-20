import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from process_kenney import inventory_archive


class KenneyCharacterBankPackagingTests(unittest.TestCase):
    def test_source_pngs_are_packaged_with_license_manifest_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_path = root / "source.zip"
            buffer = io.BytesIO()
            Image.new("RGBA", (12, 16), (120, 70, 40, 255)).save(buffer, format="PNG")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("PNG/Skin/Tint 1/tint1_head.png", buffer.getvalue())
            inventory = inventory_archive(archive_path, root / "inventory",
                                          root / "bank" / "kenney_modular_character_pack")
            bank = root / "bank" / "kenney_modular_character_pack"
            manifest = json.loads((bank / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(inventory["pngCount"], 1)
            self.assertEqual(manifest["assetCount"], 1)
            self.assertEqual(manifest["license"], "CC0-1.0")
            self.assertTrue(manifest["commercialUse"])
            self.assertTrue(manifest["apkRedistributionAllowed"])
            asset = manifest["assets"][0]
            self.assertEqual(asset["sourceFile"], "PNG/Skin/Tint 1/tint1_head.png")
            self.assertTrue((bank / asset["file"]).is_file())
            self.assertTrue((bank / "LICENSE.txt").is_file())
            self.assertTrue((bank / "SOURCE.json").is_file())


if __name__ == "__main__":
    unittest.main()
