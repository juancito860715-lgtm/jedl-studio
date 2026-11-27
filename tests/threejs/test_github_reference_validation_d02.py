import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D02.json"

class D02ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_eleven_unprotected_records_are_in_scope(self):
        keys = {record["record_key"] for record in self.data["records"]}
        self.assertEqual(len(keys), 11)
        self.assertEqual(keys, {f"D02:{i}" for i in range(8)} | {"D02:13", "D02:14", "D02:15"})

    def test_protected_crimson_records_are_not_rewritten(self):
        self.assertEqual(self.data["protected_records"]["excluded_keys"],
                         ["D02:8", "D02:9", "D02:10", "D02:11", "D02:12"])
        keys = {record["record_key"] for record in self.data["records"]}
        self.assertTrue(keys.isdisjoint(self.data["protected_records"]["excluded_keys"]))

    def test_all_records_have_math_algorithm_pseudocode_and_pinned_sources(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertTrue(all("github.com/" in url for url in record["source_files"]))

    def test_local_implementations_are_present_but_not_certified(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertEqual(record["local_adaptation_status"], "IMPLEMENTED_TESTS_PENDING")
                self.assertEqual(record["certification_status"], "PENDING_LOCAL_CI")
                self.assertIn("src/threejs/d02-procedural-geometry.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d02-procedural-geometry.test.mjs", record["implementation_files"])

    def test_summary_does_not_overstate_validation(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 11)
        self.assertEqual(summary["protected_records_preserved"], 5)
        self.assertEqual(summary["local_adaptations_implemented"], 11)
        self.assertEqual(summary["local_adaptations_tested"], 0)
        self.assertEqual(summary["certified_as_locally_operational"], 0)

if __name__ == "__main__":
    unittest.main()
