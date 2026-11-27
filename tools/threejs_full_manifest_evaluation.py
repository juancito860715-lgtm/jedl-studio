#!/usr/bin/env python3
"""Parallel, fail-closed evaluation inventory for every technique in the Three.js manifest.

This worker does not invent mathematics or certify from field presence. It inventories
technical specification gaps and links existing implementation/test evidence. Domain
workers are independent so one broken domain does not suppress the remaining results.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(".")
MANIFEST=Path("docs/threejs/Manifiesto_ThreeJS_Diccionario_Tecnico_v3_1_Integrado.json")
SPECS=Path("docs/threejs/audit/r31-technical-specifications.json")
PRESERVATION=Path("docs/threejs/audit/crimson-loong-preserved-record-map.json")
DIMENSIONS=Path("docs/threejs/audit/r31-symbol-dimension-audit.json")
POINT4=Path("docs/threejs/audit/point4-executable-validation-D35-D36.json")
RESEARCH=Path("docs/threejs/audit/external-implementation-research-D35-D36.json")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_all():
    manifest=read(MANIFEST)
    specs=read(SPECS)
    preservation=read(PRESERVATION)
    dimensions=read(DIMENSIONS)
    point4=read(POINT4) if POINT4.exists() else {"records":[]}
    research=read(RESEARCH) if RESEARCH.exists() else {"records":[]}
    return manifest,specs,preservation,dimensions,point4,research

def spec_gaps(spec):
    # Import the existing fail-closed validator so both audits use one rule set.
    from tests.threejs.implementation_readiness_gate import specification_gaps
    return specification_gaps(spec)

def make_records(domain_id=None):
    manifest,specs,preservation,dimensions,point4,research=load_all()
    spec_by={x["record_key"]:x for x in specs.get("records",[])}
    preserved={x["record_key"]:x for x in preservation.get("records",[])}
    point_by={x["record_key"]:x for x in point4.get("records",[])}
    research_by={x["record_key"]:x for x in research.get("records",[])}
    out=[]
    for d in manifest.get("domains",[]):
        if domain_id and d.get("id")!=domain_id: continue
        for index,t in enumerate(d.get("techniques") or []):
            key=f'{d.get("id")}:{index}'
            evidence=point_by.get(key,{})
            research_record=research_by.get(key,{})
            if key in preserved:
                status="PRESERVED_FAMILY_REVIEW_ONLY"
                gaps=["family-level preservation is not equation-level verification",
                      "independent implementation tests and certification remain unproven"]
            elif key in spec_by:
                spec=spec_by[key].get("technical_completion") or {}
                gaps=spec_gaps(spec)
                status="SPECIFICATION_GAPS" if gaps else "SPECIFICATION_PRESENT_IMPLEMENTATION_PENDING"
            else:
                gaps=["technical_completion record not found",
                      "source-backed implementation and independent tests not demonstrated"]
                status="TECHNICAL_SPECIFICATION_PENDING"
            implementation_status=research_record.get("status")
            if evidence.get("status")=="PRODUCTION_IMPLEMENTATION_TEST_PASSED":
                validation_tier="LOCAL_IMPLEMENTATION_TESTS_PASSED"
            elif evidence.get("status")=="REFERENCE_TEST_PASSED":
                validation_tier="REFERENCE_ORACLE_ONLY"
            else:
                validation_tier="NO_EXECUTABLE_EVIDENCE_LINKED"
            out.append({
                "record_key":key,"domain_id":d.get("id"),"domain_name":d.get("domain_name") or d.get("name"),
                "domain_index":index,"name":t.get("name"),"manifest_equation_present":bool(t.get("equation") or t.get("equations")),
                "technical_specification_status":status,"missing_or_unproven":gaps,
                "preservation_status":preserved.get(key,{}).get("preservation_status"),
                "r31_research_id":spec_by.get(key,{}).get("research_id"),
                "dimension_record_present":bool(spec_by.get(key,{}).get("research_id") and
                    any(x.get("research_id")==spec_by[key].get("research_id") for x in dimensions.get("records",[]))),
                "implementation_research_status":implementation_status,
                "execution_evidence":validation_tier,
                "implementation_file":evidence.get("implementation_file") or research_record.get("implementation"),
                "test_file":evidence.get("implementation_test_file") or research_record.get("local_tests"),
                "certification_status":"NOT_CERTIFIED"
            })
    return out

def summarize(records):
    keys=("PRESERVED_FAMILY_REVIEW_ONLY","SPECIFICATION_GAPS",
          "SPECIFICATION_PRESENT_IMPLEMENTATION_PENDING","TECHNICAL_SPECIFICATION_PENDING")
    return {k:sum(x["technical_specification_status"]==k for x in records) for k in keys}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--list-domains",action="store_true")
    p.add_argument("--domain")
    p.add_argument("--output",type=Path)
    p.add_argument("--merge",type=Path,nargs="*")
    p.add_argument("--report",type=Path,default=Path("full-manifest-evaluation.json"))
    p.add_argument("--global-test-status",type=Path)
    a=p.parse_args()
    manifest,*_=load_all()
    if a.list_domains:
        print(json.dumps([d["id"] for d in manifest["domains"] if d.get("techniques")],separators=(",",":")))
        return 0
    if a.domain:
        records=make_records(a.domain)
        payload={"domain_id":a.domain,"generated_at":datetime.now(timezone.utc).isoformat(),
                 "record_count":len(records),"counts":summarize(records),"records":records}
        target=a.output or Path(f"domain-{a.domain}.json")
        target.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"domain":a.domain,"record_count":len(records),"counts":payload["counts"]},ensure_ascii=False))
        return 0
    files=a.merge or sorted(Path("domain-results").glob("domain-*.json"))
    all_records=[]
    for f in files:
        payload=read(Path(f))
        all_records.extend(payload.get("records",[]))
    expected=sum(len(d.get("techniques") or []) for d in manifest.get("domains",[]))
    ids=[x["record_key"] for x in all_records]
    duplicate_ids=sorted({k for k in ids if ids.count(k)>1})
    missing_count=expected-len(all_records)
    global_tests={"status":"NOT_RUN"}
    if a.global_test_status and a.global_test_status.exists():
        global_tests=read(a.global_test_status)
    counts=summarize(all_records)
    certified=sum(x.get("certification_status")=="CERTIFIED" for x in all_records)
    report={
      "title":"Evaluación global automatizada del manifiesto Three.js",
      "version":"1.0.0",
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "manifest_version":manifest.get("manifest",{}).get("version"),
      "inventory":{"domains":len(manifest.get("domains",[])),"technique_records_expected":expected,
                   "technique_records_evaluated":len(all_records),"missing_records":missing_count,
                   "duplicate_record_keys":duplicate_ids,"counts_by_status":counts},
      "execution":{"domain_workers":len(files),"global_test_status":global_tests},
      "certification":{"certified":certified,"rule":"No technique is certified by this inventory workflow. Certification requires implementation-backed tests, source/license review, dimensional and mathematical review, browser/runtime validation where applicable, and independent review."},
      "records":sorted(all_records,key=lambda x:(x["domain_id"],x["domain_index"])),
      "overall_status":"INCOMPLETE" if missing_count or duplicate_ids or global_tests.get("status")!="PASS" else "EVALUATION_COMPLETE_CERTIFICATION_PENDING"
    }
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    md=["# Evaluación global del manifiesto Three.js","",
        f"- Versión: {report['manifest_version']}",
        f"- Dominios: {len(manifest.get('domains',[]))}",
        f"- Técnicas evaluadas: {len(all_records)}/{expected}",
        f"- Estado de pruebas globales: {global_tests.get('status')}",
        f"- Estado general: **{report['overall_status']}**","",
        "## Conteo por estado","",
        "| Estado | Cantidad |","|---|---:|"]
    md += [f"| {k} | {v} |" for k,v in counts.items()]
    md += ["","## Registros que requieren trabajo","",
           "| Registro | Técnica | Estado | Evidencia ejecutable |",
           "|---|---|---|---|"]
    md += [f"| {x['record_key']} | {x['name']} | {x['technical_specification_status']} | {x['execution_evidence']} |"
           for x in report["records"] if x["technical_specification_status"]!="PRESERVED_FAMILY_REVIEW_ONLY"]
    Path(str(a.report).replace(".json",".md")).write_text("\n".join(md)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False,indent=2))
    return 1 if missing_count or duplicate_ids or global_tests.get("status")=="FAIL" else 0

if __name__=="__main__":
    raise SystemExit(main())
