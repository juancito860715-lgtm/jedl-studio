import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from build_offline_bundle import build

class OfflineBundleTests(unittest.TestCase):
    def test_builds_root_manifest_with_every_payload_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            (root / "kenney").mkdir(parents=True)
            (root / "kenney" / "catalog.json").write_text(json.dumps({"license":"CC0-1.0","packCount":1}))
            with zipfile.ZipFile(root / "community-2d.zip", "w") as community:
                community.writestr("JEDL-PACKAGE.json", json.dumps({"license":"CC0-1.0","packCount":1}))
            (root / "asset.png").write_bytes(b"png-bytes")
            out = Path(temp) / "bundle.zip"
            manifest = build(root, out)
            self.assertEqual("jedl-offline-library", manifest["id"])
            self.assertEqual(3, len(manifest["files"]))
            with zipfile.ZipFile(out) as archive:
                self.assertIsNone(archive.testzip())
                root_manifest = json.loads(archive.read("JEDL-PACKAGE.json"))
                for item in root_manifest["files"]:
                    data = archive.read(item["path"])
                    self.assertEqual(item["bytes"], len(data))
                    self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest())

    def test_rejects_missing_required_catalogs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "community-2d.zip").write_bytes(b"x")
            with self.assertRaises(ValueError):
                build(root, root / "out.zip")

if __name__ == "__main__":
    unittest.main()
