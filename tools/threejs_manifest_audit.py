#!/usr/bin/env python3
"""Auditoría estructural reproducible del manifiesto Three.js.
No certifica la corrección científica de ecuaciones ni sustituye revisión de fuentes,
unidades, hipótesis, condiciones de contorno o pruebas de solver.
"""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_TECHNIQUES = 541
EXPECTED_BASELINE = 518
EXPECTED_ADDED = 23
EXPECTED_STYLES_V4 = 22

def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def audit(path: Path):
    errors = []
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("La raíz JSON debe ser un objeto.")
    domains = data.get("domains")
    if not isinstance(domains, list):
        raise ValueError("Falta el arreglo raíz 'domains'.")
    technique_records = [
        item for domain in domains if isinstance(domain, dict)
        for item in (domain.get("techniques") or []) if isinstance(item, dict)
    ]
    atlas = data.get("visual_style_atlas_v4", {})
    styles = atlas.get("styles", []) if isinstance(atlas, dict) else []
    if not isinstance(styles, list):
        styles = []
    counts = data.get("counts_v3_1", {})
    declared_total = counts.get("total_domain_technique_records")
    declared_baseline = counts.get("baseline_techniques")
    declared_added = counts.get("new_deep_techniques_added")
    declared_styles = counts.get("new_explicit_style_recipes")

    if len(technique_records) != EXPECTED_TECHNIQUES:
        errors.append(f"Registros de técnicas encontrados={len(technique_records)}; esperados={EXPECTED_TECHNIQUES}.")
    if declared_total != EXPECTED_TECHNIQUES:
        errors.append(f"counts_v3_1.total_domain_technique_records={declared_total!r}.")
    if declared_baseline != EXPECTED_BASELINE or declared_added != EXPECTED_ADDED:
        errors.append(f"Desglose esperado 518+23=541; baseline={declared_baseline!r}, añadidas={declared_added!r}.")
    if len(styles) != EXPECTED_STYLES_V4:
        errors.append(f"Recetas visual_style_atlas_v4={len(styles)}; esperadas={EXPECTED_STYLES_V4}.")
    if declared_styles != EXPECTED_STYLES_V4:
        errors.append(f"counts_v3_1.new_explicit_style_recipes={declared_styles!r}.")

    domain_ids = [d.get("id") for d in domains if isinstance(d, dict) and d.get("id")]
    style_ids = [s.get("style_id") for s in styles if isinstance(s, dict) and s.get("style_id")]
    source_ids = [o["id"] for o in walk(data) if isinstance(o.get("id"), str) and o["id"].startswith("SRC-")]
    dup_domains = sorted(k for k,v in Counter(domain_ids).items() if v > 1)
    dup_styles = sorted(k for k,v in Counter(style_ids).items() if v > 1)
    dup_sources = sorted(k for k,v in Counter(source_ids).items() if v > 1)
    if dup_domains: errors.append(f"IDs de dominio duplicados: {dup_domains}")
    if dup_styles: errors.append(f"style_id duplicados: {dup_styles}")
    if dup_sources: errors.append(f"IDs SRC duplicados: {dup_sources}")

    missing_names = [i for i,t in enumerate(technique_records) if not isinstance(t.get("name"),str) or not t["name"].strip()]
    missing_equations = [t.get("name",f"record_{i}") for i,t in enumerate(technique_records)
                         if not isinstance(t.get("equation"),str) or not t["equation"].strip()]
    refs = [sid for s in styles if isinstance(s,dict) for sid in (s.get("source_ids") or []) if isinstance(sid,str)]
    unresolved_refs = sorted(set(refs)-set(source_ids))
    report = {
      "manifest":{"title":data.get("manifest",{}).get("title"),"version":data.get("manifest",{}).get("version"),
                  "file":str(path),"bytes_utf8":len(raw.encode("utf-8")),"json_parse":"PASS"},
      "inventory":{"domains":len(domains),"technique_records_found":len(technique_records),
                   "technique_records_declared":declared_total,"baseline_techniques_declared":declared_baseline,
                   "new_techniques_declared":declared_added,"style_recipes_v4_found":len(styles),
                   "style_recipes_declared":declared_styles},
      "integrity":{"duplicate_domain_ids":dup_domains,"duplicate_style_ids":dup_styles,
                   "duplicate_source_ids":dup_sources,"technique_records_missing_name":len(missing_names),
                   "technique_records_missing_equation":len(missing_equations),
                   "unresolved_style_source_refs":unresolved_refs},
      "mathematics":{"equation_fields_present":len(technique_records)-len(missing_equations),
                     "equation_fields_missing":len(missing_equations),"missing_equation_techniques":missing_equations,
                     "coverage_status":"INCOMPLETE" if missing_equations else "EQUATION_FIELD_COVERAGE_COMPLETE",
                     "equation_correctness":"NOT_CERTIFIED",
                     "reason":"La presencia de cadenas no demuestra validez algebraica, dimensional, física ni numérica. Cada fórmula requiere fuente, hipótesis, unidades, dominio y casos de referencia independientes."},
      "preservation":{"original_records_claimed":declared_baseline,"new_records_claimed":declared_added,
                      "sum_matches_declared_total":isinstance(declared_baseline,int) and isinstance(declared_added,int) and declared_baseline+declared_added==declared_total,
                      "byte_for_byte_baseline_comparison":"NOT_PERFORMED",
                      "reason":"No existe una copia baseline independiente en el repositorio para ejecutar un diff."},
      "status":"PASS" if not errors else "FAIL","errors":errors,
      "warnings":["Los registros de técnicas no tienen necesariamente un ID propio; se auditan los namespaces de dominios, estilos y fuentes por separado.",
                  "No se ejecutó un renderer Three.js: no hay validación visual ni FPS.",
                  "No se ejecutaron solvers de física/óptica: no hay validación numérica de los modelos."]
    }
    return report, errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--report",type=Path,default=Path("threejs-manifest-audit.json"))
    a=p.parse_args()
    try: report,errors=audit(a.manifest)
    except Exception as e: report={"status":"FAIL","fatal_error":str(e)}; errors=[str(e)]
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
