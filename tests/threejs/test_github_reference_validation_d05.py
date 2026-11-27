import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D05.json"
POINT3 = ROOT / "docs/threejs/audit/point3-complete-algorithms-D05.json"

class D05ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_ten_unprotected_records_are_in_scope(self):
        keys = {r["record_key"] for r in self.data["records"]}
        expected = {"D05:0","D05:1","D05:2","D05:3","D05:4","D05:5","D05:8","D05:10","D05:11","D05:12"}
        self.assertEqual(keys, expected)

    def test_three_protected_records_are_preserved(self):
        protected = ["D05:6","D05:7","D05:9"]
        self.assertEqual(self.data["protected_records"]["excluded_keys"], protected)
        self.assertTrue({r["record_key"] for r in self.data["records"]}.isdisjoint(protected))

    def test_reference_projects_are_pinned_and_mit_licensed(self):
        projects = {p["repository"]: p for p in self.data["reference_projects"]}
        expected = ["dgreenheck/ez-tree","nylki/lindenmayer","kchapelier/poisson-disk-sampling",
                    "johnnyawesome/phyllotaxisP5JS","mrdoob/three.js","hughsk/boids"]
        for name in expected:
            with self.subTest(repository=name):
                self.assertEqual(projects[name]["license"], "MIT")
                self.assertEqual(len(projects[name]["commit"]), 40)

    def test_all_records_have_math_algorithm_and_local_test_targets(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["derivation"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertEqual(record["local_adaptation_status"], "IMPLEMENTATION_TESTS_PASSED")
                self.assertEqual(record["certification_status"], "IMPLEMENTATION_TESTS_PASSED_CERTIFICATION_PENDING")
                self.assertIn("src/threejs/d05-vegetation-ecology.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d05-vegetation-ecology.test.mjs", record["implementation_files"])

    def test_complete_algorithm_document_covers_all_open_records(self):
        point3 = json.loads(POINT3.read_text(encoding="utf-8"))
        records = point3["records"]
        self.assertEqual(len(records), 10)
        self.assertEqual({r["record_key"] for r in records},
                         {r["record_key"] for r in self.data["records"]})
        for record in records:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["inputs"])
                self.assertTrue(record["outputs"])
                self.assertTrue(record["preconditions"])
                self.assertTrue(record["algorithm_steps"])
                self.assertTrue(record["pseudocode"])

    def test_summary_does_not_claim_testing_or_certification(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 10)
        self.assertEqual(summary["protected_records_preserved"], 3)
        self.assertEqual(summary["local_adaptations_implemented"], 10)
        self.assertEqual(summary["local_adaptations_tested"], 10)
        self.assertEqual(summary["pending_local_ci"], 0)
        self.assertEqual(summary["certified_as_locally_operational"], 0)

if __name__ == "__main__":
    unittest.main()
