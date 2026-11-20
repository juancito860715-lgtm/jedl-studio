import json
import unittest
from pathlib import Path

CATALOG = Path(__file__).parent / "external_packs" / "catalog.json"


class ExternalPackCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_policy_requires_commercial_license_and_same_rig(self):
        policy = self.data["policy"]
        self.assertTrue(policy["commercialUseRequired"])
        self.assertTrue(policy["licenseEvidenceRequired"])
        self.assertTrue(policy["redistributionInApkMustBeAllowed"])
        self.assertTrue(policy["sameRigRequired"])
        self.assertTrue(policy["editorValidationRequired"])
        self.assertTrue(policy["neverInferCompatibilityFromImagePresence"])

    def test_package_ids_are_unique(self):
        ids = [item["id"] for item in self.data["packages"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_candidate_has_explicit_commercial_and_redistribution_rights(self):
        for item in self.data["packages"]:
            with self.subTest(package=item["id"]):
                self.assertTrue(item["commercialUse"])
                self.assertTrue(item["modificationAllowed"])
                self.assertTrue(item["apkRedistributionAllowed"])
                self.assertTrue(item["license"])
                self.assertTrue(item["licenseEvidence"])
                self.assertTrue(item["licenseTerms"])
                self.assertIn("not_yet_imported", item["integrationStatus"])

    def test_unvalidated_assets_cannot_be_reported_as_integrated(self):
        for item in self.data["packages"]:
            with self.subTest(package=item["id"]):
                if item["rigValidation"] != "passed" or item["editorValidation"] != "passed":
                    self.assertNotEqual(item["integrationStatus"], "integrated")

    def test_rig_and_editor_validation_start_unverified(self):
        for item in self.data["packages"]:
            with self.subTest(package=item["id"]):
                self.assertIn("rigValidation", item)
                self.assertIn("editorValidation", item)
                self.assertIn("adaptationTarget", item)


if __name__ == "__main__":
    unittest.main()
