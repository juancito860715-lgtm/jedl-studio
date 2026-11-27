import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "docs/threejs/audit/point1-dimensional-audit-D36.json"
SI_KEYS = ("L", "M", "T", "I", "Theta", "N", "J")


def valid_vector(value):
    if not isinstance(value, dict) or set(value) != set(SI_KEYS):
        return False
    for exponent in value.values():
        if isinstance(exponent, bool):
            return False
        if isinstance(exponent, (int, float)):
            if not math.isfinite(exponent):
                return False
        elif not isinstance(exponent, str) or not exponent.strip():
            return False
    return True


class TestD36DimensionalAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with AUDIT_PATH.open(encoding="utf-8") as stream:
            cls.audit = json.load(stream)

    def test_manifest_reference_and_15_techniques(self):
        self.assertEqual(self.audit["source_manifest_blob_sha"],
                         self.audit["integrity"]["manifest_blob_sha"])
        self.assertEqual(self.audit["version"], "1.1.0")
        self.assertEqual(len(self.audit["records"]), 15)

    def test_every_variable_has_seven_component_vector_or_symbolic_map(self):
        invalid = []
        for record in self.audit["records"]:
            for variable in record.get("variables", []):
                dimension = variable.get("dimension")
                if dimension == "heterogeneous_by_symbol":
                    mapping = variable.get("dimension_by_symbol", {})
                    if not mapping or any(not valid_vector(v) for v in mapping.values()):
                        invalid.append((record["record_key"], variable["symbol"]))
                elif not valid_vector(dimension):
                    invalid.append((record["record_key"], variable["symbol"]))
        self.assertEqual([], invalid)

    def test_poisson_laplacian_reduces_two_spatial_powers(self):
        variable = next(v for r in self.audit["records"] if r["record_key"] == "D36:5"
                        for v in r["variables"] if v["symbol"] == "∇²φ")
        self.assertEqual("D_phi.L - 2", variable["dimension"]["L"])
        self.assertEqual("D_phi.T", variable["dimension"]["T"])

    def test_finite_volume_flux_and_source_dimensions(self):
        record = next(r for r in self.audit["records"] if r["record_key"] == "D36:8")
        values = {v["symbol"]: v["dimension"] for v in record["variables"]}
        self.assertEqual("D_Q.L - 3", values["U"]["L"])
        self.assertEqual("D_Q.L - 2", values["F"]["L"])
        self.assertEqual("D_Q.T - 1", values["F"]["T"])
        self.assertEqual("D_Q.L - 3", values["S"]["L"])
        self.assertEqual("D_Q.T - 1", values["S"]["T"])

    def test_elasticity_stiffness_force_and_displacement_units(self):
        record = next(r for r in self.audit["records"] if r["record_key"] == "D36:9")
        values = {v["symbol"]: v["dimension"] for v in record["variables"]}
        self.assertEqual({"L": 1, "M": 0, "T": 0, "I": 0, "Theta": 0, "N": 0, "J": 0}, values["u"])
        self.assertEqual({"L": 0, "M": 1, "T": -2, "I": 0, "Theta": 0, "N": 0, "J": 0}, values["K"])
        self.assertEqual({"L": 1, "M": 1, "T": -2, "I": 0, "Theta": 0, "N": 0, "J": 0}, values["f"])


if __name__ == "__main__":
    unittest.main()
