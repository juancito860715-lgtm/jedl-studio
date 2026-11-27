import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D04.json"
POINT3 = ROOT / "docs/threejs/audit/point3-complete-algorithms-D04.json"

class D04ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_nineteen_unprotected_records_are_in_scope(self):
        keys = {r["record_key"] for r in self.data["records"]}
        expected = {f"D04:{i}" for i in range(20)} - {"D04:2"}
        self.assertEqual(keys, expected)

    def test_protected_monotone_spline_is_preserved(self):
        self.assertEqual(self.data["protected_records"]["excluded_keys"], ["D04:2"])
        self.assertNotIn("D04:2", {r["record_key"] for r in self.data["records"]})

    def test_reference_projects_have_pinned_compatible_licenses(self):
        projects = {p["repository"]: p for p in self.data["reference_projects"]}
        expected = {
            "mrdoob/three.js": "MIT",
            "pmndrs/react-spring": "MIT",
            "tangent-to/ode": "MIT",
            "mattdesl/verlet3d": "MIT",
            "hughsk/boids": "MIT",
            "avianphysics/avian": "MIT OR Apache-2.0",
            "newton-physics/newton": "Apache-2.0",
        }
        for name, license_name in expected.items():
            with self.subTest(repository=name):
                self.assertEqual(projects[name]["license"], license_name)
                self.assertEqual(len(projects[name]["commit"]), 40)

    def test_all_records_have_derivation_sources_and_local_test_targets(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["derivation"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertEqual(record["local_adaptation_status"], "IMPLEMENTATION_TESTS_PASSED")
                self.assertEqual(record["certification_status"], "IMPLEMENTATION_TESTS_PASSED_CERTIFICATION_PENDING")
                self.assertIn("src/threejs/d04-motion-simulation.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d04-motion-simulation.test.mjs", record["implementation_files"])

    def test_summary_does_not_claim_testing_or_certification(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 19)
        self.assertEqual(summary["protected_records_preserved"], 1)
        self.assertEqual(summary["local_adaptations_implemented"], 19)
        self.assertEqual(summary["local_adaptations_tested"], 19)
        self.assertEqual(summary["pending_local_ci"], 0
        self.assertEqual(summary["certified_as_locally_operational"], 0))

    def test_complete_algorithm_document_covers_all_unprotected_records(self):
        point3 = json.loads(POINT3.read_text(encoding="utf-8"))
        records = point3["records"]
        self.assertEqual(len(records), 19)
        self.assertEqual(
            {r["record_key"] for r in records},
            {r["record_key"] for r in self.data["records"]},
        )
        for record in records:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["inputs"])
                self.assertTrue(record["outputs"])
                self.assertTrue(record["preconditions"])
                self.assertTrue(record["algorithm_steps"])
                self.assertTrue(record["pseudocode"])

if __name__ == "__main__":
    unittest.main()
