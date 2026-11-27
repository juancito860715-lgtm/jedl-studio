import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D03.json"

class D03ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_eight_unprotected_records_are_in_scope(self):
        keys = {r["record_key"] for r in self.data["records"]}
        self.assertEqual(keys, {"D03:0","D03:1","D03:3","D03:13","D03:14","D03:16","D03:17","D03:18"})

    def test_eleven_protected_records_are_preserved(self):
        protected = self.data["protected_records"]["excluded_keys"]
        self.assertEqual(len(protected), 11)
        self.assertTrue({r["record_key"] for r in self.data["records"]}.isdisjoint(protected))

    def test_sources_are_pinned_to_mit_projects(self):
        projects = {p["repository"]: p for p in self.data["reference_projects"]}
        self.assertEqual(projects["mrdoob/three.js"]["license"], "MIT")
        self.assertEqual(projects["sketchpunklabs/ossos"]["license"], "MIT")
        self.assertEqual(projects["jdthaler/forte"]["license"], "MIT")
        self.assertTrue(all(len(p["commit"]) == 40 for p in projects.values()))

    def test_each_record_has_math_algorithm_and_local_test_target(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertEqual(record["local_adaptation_status"], "IMPLEMENTATION_TESTS_PASSED")
                self.assertEqual(record["certification_status"], "IMPLEMENTATION_TESTS_PASSED_CERTIFICATION_PENDING")
                self.assertIn("src/threejs/d03-character-geometry.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d03-character-geometry.test.mjs", record["implementation_files"])

    def test_summary_does_not_claim_certification(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 8)
        self.assertEqual(summary["protected_records_preserved"], 11)
        self.assertEqual(summary["local_adaptations_implemented"], 8)
        self.assertEqual(summary["local_adaptations_tested"], 8)
        self.assertEqual(summary["pending_local_ci"], 0
        self.assertEqual(summary["certified_as_locally_operational"], 0))

if __name__ == "__main__":
    unittest.main()
