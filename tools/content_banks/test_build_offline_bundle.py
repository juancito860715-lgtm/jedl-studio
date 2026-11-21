import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build_offline_bundle import build

REQUIRED_BANKS = [
    ("kenney_modular_character_pack", "characters", "Kenney Modular Character Pack"),
    ("kenney_tiny_town_objects", "objects", "Kenney Tiny Town"),
    ("kenney_foliage_objects", "objects", "Kenney Foliage Pack"),
    ("jedl_original_instruments_v1", "instruments", "Instrumentos JEDL originales"),
    ("jedl_original_clothing_v1", "clothing", "Vestuario JEDL original"),
]

def make_bank(root, bank_id, group, title):
    bank=root/"banks"/group/bank_id
    (bank/"png"/"General").mkdir(parents=True)
    raw=("png:"+bank_id).encode()
    (bank/"png"/"General"/"asset.png").write_bytes(raw)
    source="https://github.com/juancito860715-lgtm/jedl-studio"
    manifest={
        "schemaVersion":1,"id":bank_id,"title":title,"source":source,
        "license":"CC0-1.0",
        "licenseTerms":"https://creativecommons.org/publicdomain/zero/1.0/",
        "commercialUse":True,"modificationAllowed":True,"apkRedistributionAllowed":True,
        "assetCount":1,"assets":[{"id":"asset","file":"png/General/asset.png",
        "sourceFile":"PNG/General/asset.png","category":"General",
        "width":128,"height":128,"sha256":hashlib.sha256(raw).hexdigest()}]
    }
    (bank/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    (bank/"LICENSE.txt").write_text("CC0-1.0",encoding="utf-8")
    (bank/"SOURCE.json").write_text(json.dumps({"source":source,"license":"CC0-1.0"}),encoding="utf-8")

def make_all_banks(root):
    for bank_id, group, title in REQUIRED_BANKS:
        make_bank(root, bank_id, group, title)

def make_community(path, evidence=None):
    evidence=evidence or b"License: CC0-1.0\nSource: https://example.org/source\n"
    with zipfile.ZipFile(path,"w") as archive:
        archive.writestr("pack/SOURCE.md",evidence)
        manifest={
            "schemaVersion":1,"id":"community-test","license":"CC0-1.0","packCount":1,
            "packs":[{"pack":"pack","sourceUrl":"https://example.org/source",
                      "sourceLicenseStatement":"CC0-1.0","sourceEvidenceFile":"pack/SOURCE.md"}],
            "files":[{"path":"pack/SOURCE.md","bytes":len(evidence),
                      "sha256":hashlib.sha256(evidence).hexdigest()}]
        }
        archive.writestr("JEDL-PACKAGE.json",json.dumps(manifest))

class OfflineBundleTests(unittest.TestCase):
    def test_builds_root_manifest_with_all_kenney_and_jedl_bank_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"source"; root.mkdir()
            make_all_banks(root)
            make_community(root/"community-2d.zip")
            out=Path(temp)/"bundle.zip"
            manifest=build(root,out)
            self.assertEqual("jedl-offline-library",manifest["id"])
            self.assertEqual(5,manifest["bankCount"])
            self.assertEqual({x[0] for x in REQUIRED_BANKS},{x["id"] for x in manifest["banks"]})
            self.assertEqual(1,manifest["communityPackCount"])
            with zipfile.ZipFile(out) as archive:
                self.assertIsNone(archive.testzip())
                root_manifest=json.loads(archive.read("JEDL-PACKAGE.json"))
                self.assertEqual(5,root_manifest["bankCount"])
                for item in root_manifest["files"]:
                    data=archive.read(item["path"])
                    self.assertEqual(item["bytes"],len(data))
                    self.assertEqual(item["sha256"],hashlib.sha256(data).hexdigest())

    def test_rejects_missing_community_or_banks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_community(root/"community-2d.zip")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

    def test_rejects_community_metadata_that_disagrees_with_source_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_all_banks(root)
            make_community(root/"community-2d.zip", b"License: CC-BY-NC\nSource: https://example.org/source\n")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

    def test_rejects_package_missing_kenney_scene_banks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_bank(root,"jedl_original_instruments_v1","instruments","Instruments")
            make_bank(root,"jedl_original_clothing_v1","clothing","Clothing")
            make_community(root/"community-2d.zip")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

    def test_rejects_raw_source_archive_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_all_banks(root); make_community(root/"community-2d.zip")
            (root/"kenney").mkdir()
            (root/"kenney"/"unreviewed.zip").write_bytes(b"not included")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

if __name__=="__main__":
    unittest.main()
