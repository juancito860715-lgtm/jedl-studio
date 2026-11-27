import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "docs/threejs/Manifiesto_ThreeJS_Diccionario_Tecnico_v3_1_Integrado.json"
DERIVATION_PATH = ROOT / "docs/threejs/audit/point2-mathematical-derivations-D35.json"


class TestD35MonteCarloDerivation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with MANIFEST_PATH.open(encoding="utf-8") as stream:
            cls.manifest = json.load(stream)
        with DERIVATION_PATH.open(encoding="utf-8") as stream:
            cls.audit = json.load(stream)

    def test_source_equation_is_preserved_exactly(self):
        source = next(d for d in self.manifest["domains"] if d["id"] == "D35")["techniques"][12]
        record = next(r for r in self.audit["records"] if r["record_key"] == "D35:12")
        self.assertEqual(record["source_equation"], source["equation"])
        self.assertEqual(record["source_mathematical_derivation"], source["derivation"])

    def test_sample_mean_targets_expectation_under_sampling_pdf(self):
        record = next(r for r in self.audit["records"] if r["record_key"] == "D35:12")
        equations = [step["equation"] for step in record["derivation"]]
        self.assertIn("E_p[f(X)]=∫_Ω f(x)p(x)dx", equations)
        self.assertIn("Ĩ_N=(1/N)Σ_{i=1}^N f(X_i)", equations)
        self.assertTrue(any("E[Ĩ_N]" in equation for equation in equations))
        self.assertTrue(any("Var(Ĩ_N)" in equation for equation in equations))

    def test_unnormalized_integral_requires_uniform_volume_factor(self):
        record = next(r for r in self.audit["records"] if r["record_key"] == "D35:12")
        self.assertTrue(any("p(x)=1/|Ω|" in step["equation"] and "|Ω|" in step["equation"]
                            for step in record["derivation"]))
        self.assertIn("integral no normalizada", record["result"])

    def test_record_is_not_blocked_by_old_source_conflict(self):
        record = next(r for r in self.audit["records"] if r["record_key"] == "D35:12")
        self.assertNotEqual(record.get("status"), "BLOCKED_SOURCE_EQUATION_CONFLICT")
        self.assertEqual(record["source_record_key"], "D35:12")


if __name__ == "__main__":
    unittest.main()
