import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/threejs/audit/github-reference-validation-D01.json"


class D01GitHubReferenceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_manifest_domain_inventory_is_complete(self):
        records = self.data["records"]
        self.assertEqual(len(records), 8)
        self.assertEqual([r["record_key"] for r in records],
                         [f"D01:{i}" for i in range(8)])

    def test_reference_commit_and_license_are_pinned(self):
        ref = self.data["reference_project"]
        self.assertEqual(ref["repository"], "mrdoob/three.js")
        self.assertEqual(ref["commit"], "0de0346de82a0d01923ffeb27f33240ad8b4863f")
        self.assertEqual(ref["license"], "MIT")
        self.assertEqual(ref["workflow"]["conclusion"], "success")
        self.assertEqual(ref["workflow"]["head_sha"], ref["commit"])

    def test_each_record_has_mathematics_algorithm_and_pseudocode(self):
        for record in self.data["records"]:
            with self.subTest(record=record["record_key"]):
                self.assertTrue(record["mathematics"].strip())
                self.assertGreaterEqual(len(record["algorithm"]), 2)
                self.assertGreaterEqual(len(record["pseudocode"]), 30)

    def test_no_unresearched_record_is_marked_certified(self):
        for record in self.data["records"]:
            if record["local_adaptation_status"] == "NOT_RESEARCHED":
                self.assertEqual(record["certification_status"], "PENDING")

    def test_local_production_certification_is_not_overclaimed(self):
        summary = self.data["summary"]
        self.assertEqual(summary["local_adaptations_tested"], 0)
        self.assertEqual(summary["certified_as_locally_operational"], 0)


if __name__ == "__main__":
    unittest.main()
