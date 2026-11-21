import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build_offline_bundle import build

def make_bank(root):
    bank=root/"banks"/"instruments"/"test-instruments"
    (bank/"png"/"Instruments").mkdir(parents=True)
    raw=b"test-png-bytes"
    (bank/"png"/"Instruments"/"timbales.png").write_bytes(raw)
    source="https://github.com/juancito860715-lgtm/jedl-studio"
    manifest={
        "schemaVersion":1,"id":"test-instruments","title":"Test instruments",
        "source":source,"license":"CC0-1.0",
        "licenseTerms":"https://creativecommons.org/publicdomain/zero/1.0/",
        "commercialUse":True,"modificationAllowed":True,"apkRedistributionAllowed":True,
        "assetCount":1,"assets":[{"id":"timbales","file":"png/Instruments/timbales.png",
        "sourceFile":"PNG/Instruments/timbales.png","category":"Instruments",
        "width":128,"height":128,"sha256":hashlib.sha256(raw).hexdigest()}]
    }
    (bank/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    (bank/"LICENSE.txt").write_text("CC0-1.0",encoding="utf-8")
    (bank/"SOURCE.json").write_text(json.dumps({"source":source,"license":"CC0-1.0"}),encoding="utf-8")

def make_community(path):
    evidence=b"License: CC0-1.0\nSource: https://example.org/source\n"
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
    def test_builds_root_manifest_with_every_payload_hash_and_bank_license(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"source"; root.mkdir()
            make_bank(root)
            make_community(root/"community-2d.zip")
            out=Path(temp)/"bundle.zip"
            manifest=build(root,out)
            self.assertEqual("jedl-offline-library",manifest["id"])
            self.assertEqual(1,manifest["bankCount"])
            self.assertEqual("test-instruments",manifest["banks"][0]["id"])
            self.assertNotIn("kenneyPackCount",manifest)
            self.assertFalse(any(x["path"].startswith("kenney/") for x in manifest["files"]))
            with zipfile.ZipFile(out) as archive:
                self.assertIsNone(archive.testzip())
                root_manifest=json.loads(archive.read("JEDL-PACKAGE.json"))
                self.assertEqual(1,root_manifest["bankCount"])
                for item in root_manifest["files"]:
                    data=archive.read(item["path"])
                    self.assertEqual(item["bytes"],len(data))
                    self.assertEqual(item["sha256"],hashlib.sha256(data).hexdigest())

    def test_rejects_missing_community_or_banks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_community(root/"community-2d.zip")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

    def test_rejects_raw_source_archive_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_bank(root); make_community(root/"community-2d.zip")
            (root/"kenney").mkdir()
            (root/"kenney"/"unreviewed.zip").write_bytes(b"not included")
            with self.assertRaises(ValueError):
                build(root,root/"out.zip")

if __name__=="__main__":
    unittest.main()
