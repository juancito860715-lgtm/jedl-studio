import struct
import tempfile
import unittest
from pathlib import Path

from fetch_extended_sources import glb_valid, license_text, fetch, run_optional_source, require_preview_url, is_approved_grab3d_slug


def make_glb(path: Path) -> None:
    import json
    document = json.dumps({"asset": {"version": "2.0"}, "scenes": [{"nodes": []}]}).encode()
    document += b" " * ((4 - len(document) % 4) % 4)
    chunk = struct.pack("<II", len(document), 0x4E4F534A) + document
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk)


class ExtendedSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_only_individually_approved_grab3d_assets_are_eligible(self):
        self.assertTrue(is_approved_grab3d_slug("orca"))
        self.assertTrue(is_approved_grab3d_slug("cardboard-box-stack"))
        self.assertFalse(is_approved_grab3d_slug("unreviewed-model"))

    def test_accepts_valid_glb_v2(self):
        path = self.root / "valid.glb"
        make_glb(path)
        glb_valid(path)

    def test_rejects_truncated_glb(self):
        path = self.root / "bad.glb"
        path.write_bytes(b"glTF")
        with self.assertRaisesRegex(ValueError, "Truncated GLB"):
            glb_valid(path)

    def test_rejects_external_dependencies(self):
        import json
        doc = {"asset": {"version": "2.0"}, "images": [{"uri": "https://example.invalid/texture.webp"}]}
        raw = json.dumps(doc).encode()
        raw += b" " * ((4 - len(raw) % 4) % 4)
        chunk = struct.pack("<II", len(raw), 0x4E4F534A) + raw
        path = self.root / "external.glb"
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk)
        with self.assertRaisesRegex(ValueError, "External dependency"):
            glb_valid(path)

    def test_catalog_expansion_is_disabled_without_explicit_authorization(self):
        from fetch_extended_sources import main
        output = StringIO()
        with redirect_stdout(output):
            main([])
        self.assertIn("CATALOG_EXPANSION_BLOCKED", output.getvalue())
        self.assertNotIn("EXTENDED_ASSET_BANK_OK", output.getvalue())

    def test_requires_cc0_license_evidence(self):
        path = self.root / "LICENSE.txt"
        path.write_text("This is a proprietary license.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CC0 evidence"):
            license_text(path, "CC0-1.0")

    def test_optional_source_failure_is_explicit_and_non_blocking(self):
        statuses = []
        def unavailable_provider():
            raise RuntimeError("HTTP Error 403: Cloudflare challenge")
        run_optional_source("Art Institute", unavailable_provider, statuses)
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0]["status"], "deferred")
        self.assertIn("403", statuses[0]["reason"])
    def test_rejects_3d_model_without_packaged_preview_source(self):
        with self.assertRaisesRegex(ValueError, "Every 3D model must provide an HTTPS preview URL"):
            require_preview_url("", "character.tevy.casual_walker.v1")

    def test_accepts_pinned_https_preview_source(self):
        self.assertEqual(
            require_preview_url("https://tevy.dev/models/casual-walker/v1/preview.webp", "character.tevy.casual_walker.v1"),
            "https://tevy.dev/models/casual-walker/v1/preview.webp",
        )

    def test_rejects_non_https_downloads_before_network(self):
        with self.assertRaisesRegex(ValueError, "HTTPS URL required"):
            fetch("http://example.invalid/model.glb", 1024)


if __name__ == "__main__":
    unittest.main(verbosity=2)
