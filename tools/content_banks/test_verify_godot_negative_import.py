import json
import struct
import tempfile
import unittest
from pathlib import Path

from verify_godot_negative_import import (
    ci_import_gate_would_fail,
    make_meshopt_glb,
    meshopt_extension_was_rejected,
)


class GodotNegativeImportRunnerTests(unittest.TestCase):
    def test_fixture_specific_meshopt_error_proves_ci_gate_fails(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERROR: Extension EXT_meshopt_compression is not supported for "
            "res://tests/negative/incompatible.glb\n"
        )
        self.assertTrue(meshopt_extension_was_rejected(0, output))
        self.assertTrue(ci_import_gate_would_fail(0, output))

    def test_rejects_corrupt_glb_error_without_meshopt_diagnostic(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERROR: Invalid GLB JSON chunk for res://tests/negative/incompatible.glb\n"
        )
        self.assertFalse(meshopt_extension_was_rejected(0, output))

    def test_rejects_error_that_does_not_reference_fixture(self):
        output = "ERROR: Extension EXT_meshopt_compression is not supported\n"
        self.assertFalse(meshopt_extension_was_rejected(1, output))

    def test_rejects_fixture_without_importer_error(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "Import completed\n"
        )
        self.assertFalse(meshopt_extension_was_rejected(0, output))

    def test_rejects_extension_name_without_unsupported_diagnostic(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERROR: failed parsing EXT_meshopt_compression payload\n"
        )
        self.assertFalse(meshopt_extension_was_rejected(0, output))

    def test_generated_glb_has_valid_container_json_extension_and_binary_chunk(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "incompatible.glb"
            make_meshopt_glb(path)
            payload = path.read_bytes()
        magic, version, declared_length = struct.unpack_from("<4sII", payload, 0)
        self.assertEqual(magic, b"glTF")
        self.assertEqual(version, 2)
        self.assertEqual(declared_length, len(payload))
        json_length, json_type = struct.unpack_from("<II", payload, 12)
        self.assertEqual(json_type, 0x4E4F534A)
        document = json.loads(payload[20:20 + json_length].decode("utf-8").rstrip())
        self.assertEqual(document["extensionsRequired"], ["EXT_meshopt_compression"])
        self.assertEqual(document["extensionsUsed"], ["EXT_meshopt_compression"])
        extension = document["bufferViews"][0]["extensions"]["EXT_meshopt_compression"]
        self.assertEqual(extension["count"], 1)
        self.assertEqual(extension["mode"], "ATTRIBUTES")
        bin_header = 20 + json_length
        bin_length, bin_type = struct.unpack_from("<II", payload, bin_header)
        self.assertEqual(bin_type, 0x004E4942)
        self.assertEqual(bin_length, 12)
        self.assertEqual(len(payload[bin_header + 8:]), 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
