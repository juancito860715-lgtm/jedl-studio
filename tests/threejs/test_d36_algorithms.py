import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "docs/threejs/audit/point3-complete-algorithms-D36.json"
MANIFEST_PATH = ROOT / "docs/threejs/Manifiesto_ThreeJS_Diccionario_Tecnico_v3_1_Integrado.json"
EXPECTED_SOURCE_SHA = "6377a50c10f7a33797e7db45de410f864b8bac5d"


class TestD36Algorithms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with AUDIT_PATH.open(encoding="utf-8") as stream:
            cls.audit = json.load(stream)
        with MANIFEST_PATH.open(encoding="utf-8") as stream:
            cls.manifest = json.load(stream)

    def test_source_manifest_identity_and_coverage(self):
        self.assertEqual(self.audit["scope"]["source_manifest_blob_sha"], EXPECTED_SOURCE_SHA)
        source = next(d for d in self.manifest["domains"] if d["id"] == "D36")
        self.assertEqual(len(source["techniques"]), 15)
        self.assertEqual(len(self.audit["records"]), 15)

    def test_all_algorithm_fields_match_source_in_order(self):
        source = next(d for d in self.manifest["domains"] if d["id"] == "D36")
        for index, (actual, expected) in enumerate(zip(self.audit["records"], source["techniques"])):
            with self.subTest(record=f"D36:{index}"):
                self.assertEqual(actual["record_key"], f"D36:{index}")
                self.assertEqual(actual["name"], expected["name"])
                self.assertEqual(actual["source_equation"], expected["equation"])
                self.assertEqual(actual["source_derivation"], expected["derivation"])
                self.assertEqual(actual["source_parameters"], expected["parameters"])
                self.assertEqual(actual["source_variants"], expected["variants"])
                self.assertEqual(actual["algorithm_steps"], expected["algorithm"])
                self.assertEqual(actual["threejs_adaptation"], expected["threejs"])
                self.assertEqual(actual["model"], expected["model"])

    def test_pseudocode_is_exact_ordered_expansion_of_source_steps(self):
        for record in self.audit["records"]:
            expected = ["INICIO"]
            expected.extend(
                f"  PASO {index}: {step}"
                for index, step in enumerate(record["algorithm_steps"], start=1)
            )
            expected.append("FIN")
            self.assertEqual(record["pseudocode"], "\\n".join(expected))

    def test_no_record_is_mislabeled_as_implementation_certified(self):
        for record in self.audit["records"]:
            self.assertEqual(record["implementation_status"], "NOT_CERTIFIED")
            self.assertEqual(record["source_fidelity"], "VERBATIM_FIELDS_FROM_MANIFEST")


if __name__ == "__main__":
    unittest.main()
