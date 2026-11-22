import unittest

from verify_godot_negative_import import (
    ci_import_gate_would_fail,
    negative_import_was_rejected,
)


class GodotNegativeImportRunnerTests(unittest.TestCase):
    def test_fixture_specific_error_proves_ci_gate_fails_even_when_godot_exit_is_zero(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERROR: Invalid GLB JSON chunk for res://tests/negative/incompatible.glb\n"
        )
        self.assertTrue(negative_import_was_rejected(0, output))
        self.assertTrue(ci_import_gate_would_fail(0, output))

    def test_rejects_error_that_does_not_reference_fixture(self):
        output = "ERROR: unrelated project setting failure\n"
        self.assertFalse(negative_import_was_rejected(1, output))

    def test_rejects_fixture_path_without_importer_error(self):
        output = "Importing: res://tests/negative/incompatible.glb\nImport completed\n"
        self.assertFalse(negative_import_was_rejected(0, output))

    def test_rejects_importer_error_not_recognized_by_ci_gate(self):
        output = (
            "Importing: res://tests/negative/incompatible.glb\n"
            "ERR_FILE_CORRUPT: malformed resource\n"
        )
        self.assertFalse(negative_import_was_rejected(0, output))
        self.assertFalse(ci_import_gate_would_fail(0, output))

    def test_rejects_empty_output(self):
        self.assertFalse(negative_import_was_rejected(0, ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
