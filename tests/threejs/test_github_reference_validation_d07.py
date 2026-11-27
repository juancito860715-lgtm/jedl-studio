import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D07.json"
POINT3 = ROOT / "docs/threejs/audit/point3-complete-algorithms-D07.json"

class D07ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_all_twelve_records_are_in_scope(self):
        self.assertEqual({r["record_key"] for r in self.data["records"]},
                         {f"D07:{i}" for i in range(12)})

    def test_no_protected_records_were_rewritten(self):
        self.assertEqual(self.data["protected_records"]["excluded_keys"], [])

    def test_reference_projects_are_pinned_and_licensed(self):
        projects = {p["repository"]: p for p in self.data["reference_projects"]}
        expected = {
            "Aljullu/threejs-procedural-building-generator": "MIT",
            "mrdoob/three.js": "MIT",
            "avianphysics/avian": "MIT OR Apache-2.0",
            "hxtnv/citygen": "MIT",
            "tangent-to/ode": "MIT",
        }
        for name, license_name in expected.items():
            with self.subTest(repository=name):
                self.assertEqual(projects[name]["license"], license_name)
                self.assertEqual(len(projects[name]["commit"]), 40)

    def test_every_record_has_math_algorithm_source_and_test(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["derivation"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertIn("src/threejs/d07-architecture.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d07-architecture.test.mjs", record["implementation_files"])

    def test_complete_algorithm_document_covers_all_twelve(self):
        point3 = json.loads(POINT3.read_text(encoding="utf-8"))
        self.assertEqual(len(point3["records"]), 12)
        self.assertEqual({r["record_key"] for r in point3["records"]},
                         {r["record_key"] for r in self.data["records"]})
        for record in point3["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["inputs"])
                self.assertTrue(record["outputs"])
                self.assertTrue(record["preconditions"])
                self.assertTrue(record["algorithm_steps"])
                self.assertTrue(record["pseudocode"])

    def test_summary_does_not_claim_testing_or_certification(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 12)
        self.assertEqual(summary["local_adaptations_implemented"], 12)
        self.assertEqual(summary["local_adaptations_tested"], 0)
        self.assertEqual(summary["certified_as_locally_operational"], 0)

if __name__ == "__main__":
    unittest.main()
