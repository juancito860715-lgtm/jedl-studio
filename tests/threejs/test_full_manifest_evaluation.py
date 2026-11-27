import unittest
from tools.threejs_full_manifest_evaluation import spec_gaps

class TestManifestEvaluationDerivationScopes(unittest.TestCase):
    def minimal_spec(self, status):
        return {
            "formulation_type": "scoped_kernel",
            "variables": [{"symbol":"x","meaning":"position","dimension":{"L":1,"M":0,"T":0,"I":0,"Theta":0,"N":0,"J":0},"unit":"m","domain":"finite"}],
            "equations": [{"expression":"x=x","dimensional_check":"pass","status":"derived_and_checked"}],
            "derivation": {"status":status,"steps":["Define the input state.","Apply the stated projection/update.","Return the resulting state."]},
            "assumptions": ["finite inputs"], "valid_domain": ["finite values"],
            "boundary_conditions": ["zero input is handled"], "inputs": ["x"],
            "outputs": ["x"], "algorithm_steps": ["validate","compute","return"],
            "pseudocode": "validate(x); y = update(x); return y",
            "complexity": {"time":"O(1)","space":"O(1)"},
            "implementation_mapping": {"threejs_api":"CPU kernel","cpu_reference":"reference function","gpu_strategy":"optional shader port"},
            "source_claims": [{"url":"https://example.org/source","supported_claim":"the stated kernel","formula_locator":"section 1","formula_level_status":"verified"}],
            "independent_tests": {"python":["analytic fixture"],"javascript":["parity fixture"],"edge_cases":["zero"]}
        }

    def test_scoped_core_derivation_is_not_misreported_as_missing(self):
        for status in ("complete_for_core_kernel", "complete_for_project_authored_hash_kernel",
                       "COMPLETE_FOR_SINGLE_PERIODIC_HATCH_FAMILY",
                       "complete", "not_applicable"):
            with self.subTest(status=status):
                self.assertNotIn("derivation.complete_steps", spec_gaps(self.minimal_spec(status)))

    def test_partial_derivation_remains_a_gap_even_when_steps_exist(self):
        self.assertIn("derivation.complete_steps", spec_gaps(self.minimal_spec("partial")))

    def test_missing_steps_remain_a_gap(self):
        spec=self.minimal_spec("complete_for_core_kernel")
        spec["derivation"]["steps"]=[]
        self.assertIn("derivation.complete_steps", spec_gaps(spec))

if __name__ == "__main__":
    unittest.main()
