import hashlib, json, struct, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from generate_instrument_bank import generate

class InstrumentBankTests(unittest.TestCase):
    def test_generates_11_original_cc0_png_instruments_with_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"content/instruments/jedl_original_instruments_v1"
            with patch("generate_instrument_bank.ROOT",root): entries=generate()
            manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(11,len(entries)); self.assertEqual(11,manifest["assetCount"])
            self.assertEqual("CC0-1.0",manifest["license"])
            self.assertTrue(manifest["commercialUse"] and manifest["modificationAllowed"] and manifest["apkRedistributionAllowed"])
            for item in entries:
                raw=(root/item["file"]).read_bytes()
                self.assertEqual(b"\x89PNG\r\n\x1a\n",raw[:8])
                self.assertEqual((128,128),struct.unpack(">II",raw[16:24]))
                self.assertEqual(item["sha256"],hashlib.sha256(raw).hexdigest())
                self.assertEqual("Instruments",item["category"])
if __name__=="__main__": unittest.main()
