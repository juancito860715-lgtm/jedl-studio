import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "docs/threejs/audit/point1-dimensional-audit-D35.json"
SI_KEYS = ("L", "M", "T", "I", "Theta", "N", "J")

# The 38 entries that previously used generic labels such as "tipado",
# "por componente" or "normalizado". Each must now expose a seven-component
# SI vector, or a per-symbol map of seven-component vectors.
EXPECTED_COMPLETED = {
    "D35:0|e", "D35:0|u", "D35:0|Kp,Ki,Kd",
    "D35:3|x", "D35:3|A,H", "D35:3|z", "D35:3|w,v",
    "D35:3|P,Q,R", "D35:3|K",
    "D35:4|θ", "D35:4|E", "D35:4|∇E", "D35:4|η",
    "D35:5|r", "D35:5|J", "D35:5|λ", "D35:5|Δ",
    "D35:6|x", "D35:6|f", "D35:6|f'", "D35:6|x_next",
    "D35:7|a,b,m", "D35:7|f(a),f(b)", "D35:7|ε_x",
    "D35:8|t", "D35:8|a,b,c,d", "D35:8|p(t)",
    "D35:9|a0,an,bn", "D35:9|f(t)",
    "D35:10|x_n", "D35:10|X_k",
    "D35:11|f(t)", "D35:11|W",
    "D35:12|x_i", "D35:12|p(x)", "D35:12|f(x)",
    "D35:13|P(k)", "D35:14|L_i",
}


def is_seven_component_vector(value):
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


class TestD35DimensionalAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with AUDIT_PATH.open(encoding="utf-8") as stream:
            cls.audit = json.load(stream)

    def test_manifest_reference_is_v35(self):
        self.assertEqual(self.audit["source_manifest_blob_sha"],
                         self.audit["integrity"]["manifest_blob_sha"])
        self.assertEqual(self.audit["version"], "1.2.0")

    def test_all_38_previously_incomplete_definitions_are_present(self):
        actual = {
            f'{record["record_key"]}|{variable["symbol"]}'
            for record in self.audit["records"]
            for variable in record.get("variables", [])
        }
        self.assertEqual(EXPECTED_COMPLETED, EXPECTED_COMPLETED & actual)
        self.assertEqual(len(EXPECTED_COMPLETED), 38)

    def test_every_variable_has_explicit_seven_component_dimensions(self):
        invalid = []
        for record in self.audit["records"]:
            for variable in record.get("variables", []):
                dimension = variable.get("dimension")
                if dimension == "heterogeneous_by_symbol":
                    mapping = variable.get("dimension_by_symbol", {})
                    if not mapping or any(
                        not is_seven_component_vector(vector)
                        for vector in mapping.values()
                    ):
                        invalid.append((record["record_key"], variable["symbol"]))
                elif not is_seven_component_vector(dimension):
                    invalid.append((record["record_key"], variable["symbol"]))
        self.assertEqual([], invalid)

    def test_heterogeneous_grouped_symbols_are_separated(self):
        expected = {
            ("D35:0", "Kp,Ki,Kd"): {"Kp", "Ki", "Kd"},
            ("D35:3", "A,H"): {"A_ij", "H_ij"},
            ("D35:3", "w,v"): {"w_i", "v_i"},
            ("D35:3", "P,Q,R"): {"P_ij", "Q_ij", "R_ij"},
            ("D35:7", "a,b,m"): {"a", "b", "m"},
            ("D35:7", "f(a),f(b)"): {"f(a)", "f(b)"},
            ("D35:8", "t"): {"t_normalized", "t_seconds"},
        }
        for record_id, symbol, in expected:
            variable = next(
                v for r in self.audit["records"] if r["record_key"] == record_id
                for v in r["variables"] if v["symbol"] == symbol
            )
            self.assertEqual(expected[(record_id, symbol)],
                             set(variable["dimension_by_symbol"]))

    def test_radiance_si_base_dimension_is_correct(self):
        variable = next(
            v for r in self.audit["records"] if r["record_key"] == "D35:14"
            for v in r["variables"] if v["symbol"] == "L_i"
        )
        self.assertEqual(
            {"L": 0, "M": 1, "T": -3, "I": 0, "Theta": 0, "N": 0, "J": 0},
            variable["dimension"],
        )

    def test_lm_lambda_requires_residual_squared_dimension(self):
        variable = next(
            v for r in self.audit["records"] if r["record_key"] == "D35:5"
            for v in r["variables"] if v["symbol"] == "λ"
        )
        self.assertEqual("2*D_r.L", variable["dimension"]["L"])
        self.assertEqual("2*D_r.T", variable["dimension"]["T"])


if __name__ == "__main__":
    unittest.main()
