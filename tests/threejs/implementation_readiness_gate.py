#!/usr/bin/env python3
"""Fail-closed readiness gate for the Three.js technique manifest.

This tool never attempts to invent formulas. It checks whether each technique has
an evidence-backed specification. Crimson Loong records listed in the preservation
map are excluded from re-audit and retained as PRESERVED_CRIMSON_LOONG.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED = (
    "formulation_type", "variables", "equations", "derivation", "assumptions",
    "valid_domain", "boundary_conditions", "inputs", "outputs", "algorithm_steps",
    "pseudocode", "complexity", "implementation_mapping", "source_claims",
    "independent_tests",
)

def specification_gaps(spec):
    gaps=[]
    for key in REQUIRED:
        value=spec.get(key)
        if value is None or value == "" or value == []:
            gaps.append(key)
    variables=spec.get("variables") or []
    if not variables:
        gaps.append("variables.symbol_table")
    else:
        for i,v in enumerate(variables):
            for k in ("symbol","meaning","dimension","unit","domain"):
                if not v.get(k):
                    gaps.append(f"variables[{i}].{k}")
    deriv=spec.get("derivation") or {}
    if deriv.get("status") not in ("complete","not_applicable") or not deriv.get("steps"):
        gaps.append("derivation.complete_steps")
    equations=spec.get("equations") or []
    if not equations:
        gaps.append("equations.normalized")
    for i,e in enumerate(equations):
        if e.get("dimensional_check") != "pass":
            gaps.append(f"equations[{i}].dimensional_check")
        if e.get("status") not in ("source_verified","derived_and_checked","approximation","authored_convention"):
            gaps.append(f"equations[{i}].evidence_status")
    tests=spec.get("independent_tests") or {}
    for lang in ("python","javascript","edge_cases"):
        if not tests.get(lang):
            gaps.append(f"independent_tests.{lang}")
    for i,s in enumerate(spec.get("source_claims") or []):
        for k in ("url","supported_claim","formula_locator","formula_level_status"):
            if not s.get(k):
                gaps.append(f"source_claims[{i}].{k}")
        if s.get("formula_level_status") not in ("verified","authored_convention"):
            gaps.append(f"source_claims[{i}].formula_level_status")
    impl=spec.get("implementation_mapping") or {}
    for k in ("threejs_api","cpu_reference","gpu_strategy"):
        if not impl.get(k):
            gaps.append(f"implementation_mapping.{k}")
    algo=spec.get("algorithm_steps") or []
    if len(algo)<2:
        gaps.append("algorithm_steps.complete_sequence")
    pseudo=spec.get("pseudocode") or ""
    if len(pseudo.strip())<40:
        gaps.append("pseudocode.executable_detail")
    complexity=spec.get("complexity") or {}
    if not complexity.get("time") or not complexity.get("space"):
        gaps.append("complexity.time_and_space")
    return sorted(set(gaps))

def audit(manifest_path, r31_path, preservation_path, register_path):
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    r31=json.loads(Path(r31_path).read_text(encoding="utf-8"))
    preservation=json.loads(Path(preservation_path).read_text(encoding="utf-8"))
    preserved={x["record_key"] for x in preservation.get("records",[])}
    specs={x["record_key"]:x for x in r31.get("records",[])}
    records=[]
    for d in manifest.get("domains",[]):
        for i,t in enumerate(d.get("techniques",[])):
            key=f'{d["id"]}:{i}'
            if key in preserved:
                status="PRESERVED_CRIMSON_LOONG"
                gaps=[]
            elif key in specs:
                spec=specs[key]["technical_completion"]
                gaps=specification_gaps(spec)
                status="IMPLEMENTATION_READY" if not gaps else "INCOMPLETE"
            else:
                status="INCOMPLETE"
                gaps=["complete_technical_specification_not_created"]
            records.append({"record_key":key,"name":t.get("name"),"research_id":t.get("research_id"),
                            "status":status,"gaps":gaps})
    false_ready=[x for x in records if x["status"]=="IMPLEMENTATION_READY" and x["gaps"]]
    counts={s:sum(x["status"]==s for x in records) for s in
            ("IMPLEMENTATION_READY","INCOMPLETE","PRESERVED_CRIMSON_LOONG")}
    report={"title":"Fail-closed implementation readiness audit","version":"1.0.0",
            "manifest_technique_count":len(records),"counts":counts,
            "preserved_records_are_exempt_from_reaudit":True,
            "false_ready_records":false_ready,"records":records,
            "status":"PASS" if len(records)==541 and not false_ready else "FAIL",
            "meaning":"PASS means no incomplete technique was falsely promoted to ready; it does not mean all techniques are ready."}
    Path(register_path).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--r31",required=True)
    p.add_argument("--preservation",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    report=audit(a.manifest,a.r31,a.preservation,a.report)
    print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False,indent=2))
    return 0 if report["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
