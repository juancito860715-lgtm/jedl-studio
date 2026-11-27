import unittest
from implementation_readiness_gate import specification_gaps, validate_dimensional_audit

class TestImplementationReadinessGate(unittest.TestCase):
    def test_incomplete_spec_is_never_ready(self):
        gaps=specification_gaps({"equations":[{"expression":"x=y","dimensional_check":"pending"}]})
        self.assertIn("variables.symbol_table",gaps)
        self.assertIn("derivation.complete_steps",gaps)
        self.assertIn("equations[0].dimensional_check",gaps)
        self.assertIn("independent_tests.python",gaps)

    def test_complete_evidence_shape_has_no_gaps(self):
        spec={
          "formulation_type":"geometric_method",
          "variables":[{"symbol":"x","meaning":"position","dimension":{"L":1,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0},"unit":"m","domain":"R^3"}],
          "equations":[{"id":"eq1","expression":"x=x0+v*t","purpose":"advance position","status":"derived_and_checked","dimensional_check":"pass"}],
          "derivation":{"status":"complete","steps":["Start from dx/dt=v","Integrate over dt for constant v"]},
          "assumptions":["v constant over the step"],"valid_domain":["finite dt"],"boundary_conditions":["no boundary in free space"],
          "inputs":[{"name":"x0","type":"Vector3","unit":"m","constraints":"finite"}],
          "outputs":[{"name":"x1","type":"Vector3","unit":"m"}],
          "algorithm_steps":["validate inputs","compute displacement","return updated position"],
          "pseudocode":"validate finite x0,v,dt; return x0 + v*dt",
          "complexity":{"time":"O(1)","space":"O(1)"},
          "implementation_mapping":{"threejs_api":"Vector3.addScaledVector","cpu_reference":"pure function","gpu_strategy":"vertex shader equivalent"},
          "source_claims":[{"url":"https://example.org/paper","supported_claim":"constant-velocity integration","formula_locator":"section 2 equation 1","formula_level_status":"verified"}],
          "independent_tests":{"python":["analytic x(2)=6"],"javascript":["same analytic oracle"],"edge_cases":["dt=0"]}
        }
        self.assertEqual(specification_gaps(spec),[])

    def test_dimensional_audit_requires_complete_SI_dimension_vectors(self):
        payload={"records":[{"research_id":"R31-X","variables":[{"symbol":"x","meaning":"position","unit":"m","domain":"finite","dimension":{"L":1,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0}}]}]}
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"PASS")
        payload["records"][0]["variables"][0]["dimension"].pop("T")
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"FAIL")

    def test_authored_rule_must_be_explicitly_labelled(self):
        spec={"source_claims":[{"url":"https://example.org","supported_claim":"claim","formula_locator":"none","formula_level_status":"not_verified"}]}
        gaps=specification_gaps(spec)
        self.assertIn("source_claims[0].formula_level_status",gaps)

if __name__=="__main__":
    unittest.main()
