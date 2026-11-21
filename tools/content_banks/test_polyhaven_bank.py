import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).with_name("fetch_polyhaven.py")
SPEC = importlib.util.spec_from_file_location("fetch_polyhaven", SCRIPT)
bank = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bank)


class PolyHavenBankTests(unittest.TestCase):
    def test_gltf_selection_prefers_smallest_available_resolution(self):
        files = {
            "gltf": {
                "4k": {"gltf": {"url": "https://example.test/model_4k.gltf"}},
                "1k": {"gltf": {"url": "https://example.test/model_1k.gltf"}},
                "2k": {"gltf": {"url": "https://example.test/model_2k.gltf"}},
            }
        }
        self.assertTrue(bank.choose_gltf_file(files)["url"].endswith("model_1k.gltf"))

    def test_model_include_paths_reject_traversal_and_absolute_paths(self):
        self.assertEqual(bank.safe_relative_path("textures/albedo.png").as_posix(),
                         "textures/albedo.png")
        for unsafe in ("../outside.bin", "/outside.bin", "textures/../../outside.bin"):
            with self.subTest(path=unsafe), self.assertRaises(ValueError):
                bank.safe_relative_path(unsafe)

    def test_photographic_assets_are_downsampled_to_mobile_friendly_jpeg(self):
        source = Image.new("RGB", (4096, 2048), (30, 90, 40))
        import io
        payload = io.BytesIO()
        source.save(payload, format="JPEG")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "forest.jpg"
            width, height = bank.save_jpeg(payload.getvalue(), output, 2048)
            self.assertEqual((width, height), (2048, 1024))
            with Image.open(output) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.size, (2048, 1024))
            self.assertEqual(len(bank.sha256(output)), 64)


if __name__ == "__main__":
    unittest.main()
