import unittest

from verify_godot_negative_import import negative_import_was_rejected


class GodotNegativeImportRunnerTests(unittest.TestCase):
    def test_accepts_fixture_specific_importer_error_even_when_godot_exit_is_zero(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERROR: Invalid GLB JSON chunk for res://tests/negative/incompatible.glb\n"
        )
        self.assertTrue(negative_import_was_rejected(0, output))

    def test_rejects_error_that_does_not_reference_fixture(self):
        output = "ERROR: unrelated project setting failure\n"
        self.assertFalse(negative_import_was_rejected(1, output))

    def test_rejects_fixture_path_without_importer_error(self):
        output = "Importing: res://tests/negative/incompatible.glb\nImport completed\n"
        self.assertFalse(negative_import_was_rejected(0, output))

    def test_rejects_empty_output(self):
        self.assertFalse(negative_import_was_rejected(0, ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
