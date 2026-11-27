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

    def test_dimensional_audit_rejects_known_unit_dimension_mismatch(self):
        payload={"records":[{"research_id":"R31-X","variables":[{"symbol":"x","meaning":"position","unit":"m","domain":"finite","dimension":{"L":0,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0}}]}]}
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["invalid_entries"][0]["reason"],"unit_dimension_mismatch")

    def test_pixel_coordinate_unit_is_consistent_image_space_length(self):
        payload={"records":[{"research_id":"R31-X","variables":[{"symbol":"sigma","meaning":"pixel radius","unit":"pixels","domain":"positive","dimension":{"L":1,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0}}]}]}
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["unit_audit"]["status"],"PASS")
        self.assertEqual(result["unit_audit"]["checked_known_units"],1)

    def test_dimensional_audit_marks_custom_units_as_conditional(self):
        payload={"records":[{"research_id":"R31-X","variables":[{"symbol":"x","meaning":"pixel intensity","unit":"intensity/pixel","domain":"finite","dimension":{"L":0,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0}}]}]}
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["unit_audit"]["status"],"CONDITIONAL")
        self.assertEqual(len(result["unit_audit"]["unresolved_units"]),1)

    def test_dimensional_audit_rejects_duplicate_ids_and_nonfinite_exponents(self):
        variable={"symbol":"x","meaning":"position","unit":"m","domain":"finite","dimension":{"L":1,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0}}
        bad=dict(variable);bad["dimension"]={**variable["dimension"],"L":float("nan")}
        payload={"records":[{"research_id":"R31-X","variables":[variable]},{"research_id":"R31-X","variables":[bad]}]}
        result=validate_dimensional_audit(payload,["R31-X"])
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["duplicate_research_ids"],["R31-X"])
        self.assertTrue(any(x["reason"]=="dimension_exponents_must_be_finite_numbers" for x in result["invalid_entries"]))

    def test_malformed_source_claim_is_reported_not_crashes(self):
        spec={"source_claims":[["not","an","object"]]}
        gaps=specification_gaps(spec)
        self.assertIn("source_claims[0].must_be_object",gaps)

    def test_authored_rule_must_be_explicitly_labelled(self):
        spec={"source_claims":[{"url":"https://example.org","supported_claim":"claim","formula_locator":"none","formula_level_status":"not_verified"}]}
        gaps=specification_gaps(spec)
        self.assertIn("source_claims[0].formula_level_status",gaps)

if __name__=="__main__":
    unittest.main()
