"""Fail-closed coverage map: every one of the 23 R31 records must name real tests."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/"docs/threejs/audit/r31-oracle-coverage.json"
PY_FILES=[ROOT/"tests/threejs/test_r31_math_kernels.py",ROOT/"tests/threejs/test_r31_completion_kernels.py"]
JS_FILES=[ROOT/"tests/threejs/r31_kernels.test.mjs",ROOT/"tests/threejs/r31_completion_kernels.test.mjs"]

class TestR31OracleCoverage(unittest.TestCase):
    def test_all_23_records_have_existing_python_and_javascript_oracles(self):
        payload=json.loads(MAP.read_text(encoding="utf-8"))
        specs=json.loads((ROOT/"docs/threejs/audit/r31-technical-specifications.json").read_text(encoding="utf-8"))
        self.assertEqual({r["research_id"] for r in payload["records"]},{r["research_id"] for r in specs["records"]})
        self.assertEqual(payload["count"],23)
        self.assertEqual(len(payload["records"]),23)
        ids=[r["research_id"] for r in payload["records"]]
        self.assertEqual(len(ids),len(set(ids)))
        py_text="\n".join(p.read_text(encoding="utf-8") for p in PY_FILES)
        js_text="\n".join(p.read_text(encoding="utf-8") for p in JS_FILES)
        py_names=set(re.findall(r"def (test_[A-Za-z0-9_]+)\(",py_text))
        js_names=set(re.findall(r'test\("([^"]+)"',js_text))
        for record in payload["records"]:
            with self.subTest(research_id=record["research_id"]):
                self.assertTrue(record["python_tests"])
                self.assertTrue(record["javascript_tests"])
                self.assertTrue(record["oracle_basis"])
                for name in record["python_tests"]:
                    self.assertIn(name,py_names,f"missing Python test: {name}")
                for name in record["javascript_tests"]:
                    self.assertIn(name,js_names,f"missing JavaScript test: {name}")

if __name__=="__main__":
    unittest.main()
