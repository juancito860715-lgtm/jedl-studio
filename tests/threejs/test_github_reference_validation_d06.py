import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/threejs/audit/github-reference-validation-D06.json"
POINT3 = ROOT / "docs/threejs/audit/point3-complete-algorithms-D06.json"

class D06ReferenceValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_eight_unprotected_records_are_in_scope(self):
        expected = {"D06:0","D06:2","D06:3","D06:5","D06:6","D06:9","D06:10","D06:11"}
        self.assertEqual({r["record_key"] for r in self.data["records"]}, expected)

    def test_four_protected_records_are_preserved(self):
        protected = ["D06:1","D06:4","D06:7","D06:8"]
        self.assertEqual(self.data["protected_records"]["excluded_keys"], protected)
        self.assertTrue({r["record_key"] for r in self.data["records"]}.isdisjoint(protected))

    def test_reference_projects_are_pinned_and_mit_licensed(self):
        projects = {p["repository"]: p for p in self.data["reference_projects"]}
        expected = ["mrdoob/three.js","djorna/terrain-generation","dgreenheck/ez-tree",
                    "tcoppex/barbu","zhaijialong/RealEngine"]
        for name in expected:
            with self.subTest(repository=name):
                self.assertEqual(projects[name]["license"], "MIT")
                self.assertEqual(len(projects[name]["commit"]), 40)

    def test_all_records_have_math_algorithms_and_tests(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"])
                self.assertTrue(record["derivation"])
                self.assertTrue(record["algorithm"])
                self.assertTrue(record["pseudocode"])
                self.assertTrue(record["source_files"])
                self.assertIn("src/threejs/d06-terrain-erosion.mjs", record["implementation_files"])
                self.assertIn("tests/threejs/d06-terrain-erosion.test.mjs", record["implementation_files"])

    def test_hair_scattering_is_not_misrepresented_as_complete(self):
        hair = next(r for r in self.data["records"] if r["record_key"] == "D06:11")
        self.assertEqual(hair["local_adaptation_status"], "APPROXIMATION_TESTS_PASSED_MODEL_INCOMPLETE")
        self.assertEqual(hair["certification_status"], "PENDING_FULL_MARSCHNER_MODEL")
        self.assertIn("not", hair["implementation_note"].lower())

    def test_complete_algorithm_document_covers_all_open_records(self):
        point3 = json.loads(POINT3.read_text(encoding="utf-8"))
        self.assertEqual(len(point3["records"]), 8)
        self.assertEqual({r["record_key"] for r in point3["records"]},
                         {r["record_key"] for r in self.data["records"]})
        for record in point3["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["inputs"])
                self.assertTrue(record["outputs"])
                self.assertTrue(record["preconditions"])
                self.assertTrue(record["algorithm_steps"])
                self.assertTrue(record["pseudocode"])

    def test_summary_does_not_claim_certification(self):
        summary = self.data["summary"]
        self.assertEqual(summary["records_in_scope"], 8)
        self.assertEqual(summary["protected_records_preserved"], 4)
        self.assertEqual(summary["local_adaptations_implemented"], 8)
        self.assertEqual(summary["local_adaptations_tested"], 8)
        self.assertEqual(summary["pending_local_ci"], 0)
        self.assertEqual(summary["pending_model_completeness"], 1)
        self.assertEqual(summary["certified_as_locally_operational"], 0)

if __name__ == "__main__":
    unittest.main()
