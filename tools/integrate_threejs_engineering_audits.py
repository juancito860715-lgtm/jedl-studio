#!/usr/bin/env python3
"""Integrate repository engineering audits into the single-file Three.js manifest.

The merge is idempotent, name/key based, preserves every original technique field,
and never upgrades a technique to certified merely because tests passed.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(".")
MANIFEST = ROOT / "docs/threejs/Manifiesto_ThreeJS_v3_5_jedl-studio.json"
AUDIT = ROOT / "docs/threejs/audit"

FILES = {
    "D13_P1": "point1-dimensional-audit-D13.json",
    "D13_P2": "point2-mathematical-derivations-D13.json",
    "D35_P1": "point1-dimensional-audit-D35.json",
    "D35_P2": "point2-mathematical-derivations-D35.json",
    "D35_P3": "point3-complete-algorithms-D35.json",
    "D36_P1": "point1-dimensional-audit-D36.json",
    "D36_P2": "point2-mathematical-derivations-D36.json",
    "D36_P3": "point3-complete-algorithms-D36.json",
    "P4": "point4-executable-validation-D35-D36.json",
    "RESEARCH": "external-implementation-research-D35-D36.json",
    "EXECUTION": "latest-execution-evidence.json",
}

def read_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)

def records(path: Path):
    payload = read_json(path)
    return payload.get("records", [])

def by_key(path: Path):
    return {record["record_key"]: record for record in records(path)}

def by_name(path: Path):
    return {record["name"]: record for record in records(path)}

def attach(target, field, record, source):
    target.setdefault("engineering_audit", {})[field] = record
    target["engineering_audit"]["integration_source"] = source
    target["engineering_audit"]["certification_status"] = "NOT_CERTIFIED"
    target["engineering_audit"]["certification_note"] = (
        "La integración documental y las pruebas registradas no equivalen a "
        "certificación matemática independiente ni a validación completa de runtime."
    )

def main():
    manifest = read_json(MANIFEST)
    domains = {item["id"]: item for item in manifest["domains"]}
    expected_domains = 42
    expected_techniques = 616
    assert len(domains) == expected_domains
    assert sum(len(item.get("techniques", [])) for item in domains.values()) == expected_techniques

    loaded = {key: AUDIT / filename for key, filename in FILES.items()}
    for path in loaded.values():
        if not path.exists():
            raise FileNotFoundError(path)

    coverage = {
        "D13": {"point1": 0, "point2": 0, "point3": "not_found",
                "source_records_point1": 0, "source_records_point2": 0,
                "reassigned_to_other_domain": [], "unmatched_records": []},
        "D35": {"point1": 0, "point2": 0, "point3": 0, "point4": 0,
                "implemented_local_ci_passed": []},
        "D36": {"point1": 0, "point2": 0, "point3": 0, "point4": 0,
                "implemented_local_ci_passed": []},
    }

    # D13 audit files were produced against a historical 16-record ordering.
    # Resolve by exact technique name, never by index.
    d13_p1 = by_name(loaded["D13_P1"])
    d13_p2 = by_name(loaded["D13_P2"])
    coverage["D13"]["source_records_point1"] = len(d13_p1)
    coverage["D13"]["source_records_point2"] = len(d13_p2)
    for source_map, field, source_name in (
        (d13_p1, "point1_dimensional_audit", FILES["D13_P1"]),
        (d13_p2, "point2_mathematical_derivation", FILES["D13_P2"]),
    ):
        for name, record in source_map.items():
            target_domain = "D13"
            target = next((t for t in domains["D13"]["techniques"] if t["name"] == name), None)
            if target is None:
                target_domain = "D02"
                target = next((t for t in domains.get("D02", {}).get("techniques", [])
                               if t["name"] == name), None)
            if target is None:
                coverage["D13"]["unmatched_records"].append({
                    "source_record_key": record.get("record_key"),
                    "name": name,
                    "source_file": source_name
                })
                continue
            attach(target, field, record, source_name)
            if target_domain == "D13":
                coverage["D13"]["point1" if field.startswith("point1") else "point2"] += 1
            else:
                item = {"source_record_key": record.get("record_key"), "name": name,
                        "target_domain": target_domain,
                        "reason": "Correspondencia exacta por nombre; la ficha pertenece a D02 en v3.5."}
                if item not in coverage["D13"]["reassigned_to_other_domain"]:
                    coverage["D13"]["reassigned_to_other_domain"].append(item)

    # D35 and D36 use stable record_key values and verify names against the
    # current manifest before attaching any audit material.
    for domain_id in ("D35", "D36"):
        source_specs = (
            ("point1_dimensional_audit", f"{domain_id}_P1", "point1"),
            ("point2_mathematical_derivation", f"{domain_id}_P2", "point2"),
            ("point3_complete_algorithm", f"{domain_id}_P3", "point3"),
        )
        for field, file_key, count_key in source_specs:
            for key, record in by_key(loaded[file_key]).items():
                prefix, raw_index = key.split(":")
                index = int(raw_index)
                if prefix != domain_id or index >= len(domains[domain_id]["techniques"]):
                    raise ValueError(f"Clave fuera de dominio: {key}")
                target = domains[domain_id]["techniques"][index]
                if target["name"] != record["name"]:
                    raise ValueError(f"Desajuste de identidad {key}: {target['name']} != {record['name']}")
                attach(target, field, record, FILES[file_key])
                coverage[domain_id][count_key] += 1

        for key, record in by_key(loaded["P4"]).items():
            if not key.startswith(domain_id + ":"):
                continue
            index = int(key.split(":")[1])
            target = domains[domain_id]["techniques"][index]
            if target["name"] != record["name"]:
                raise ValueError(f"Desajuste punto 4 {key}")
            attach(target, "point4_executable_validation", record, FILES["P4"])
            coverage[domain_id]["point4"] += 1

        for key, record in by_key(loaded["RESEARCH"]).items():
            if not key.startswith(domain_id + ":"):
                continue
            index = int(key.split(":")[1])
            target = domains[domain_id]["techniques"][index]
            if target["name"] != record["name"]:
                raise ValueError(f"Desajuste investigación {key}")
            attach(target, "external_implementation_research", record, FILES["RESEARCH"])
            if record.get("status") == "IMPLEMENTED_AND_LOCAL_CI_PASSED":
                evidence = {
                    "status": record["status"],
                    "implementation_file": record.get("implementation"),
                    "test_file": record.get("local_tests"),
                    "source": record.get("source"),
                    "execution_run": record.get("execution_run"),
                    "execution_sha": record.get("execution_sha"),
                    "local_ci": record.get("local_ci"),
                }
                target["engineering_audit"]["implementation_evidence"] = evidence
                coverage[domain_id]["implemented_local_ci_passed"].append({
                    "record_key": key, "name": record["name"],
                    "implementation_file": record.get("implementation"),
                    "test_file": record.get("local_tests"),
                    "execution_run": record.get("execution_run"),
                })

    # Keep D13's original algorithm_steps and pseudocode intact. No independent
    # point-3 D13 audit file exists in the repository evidence set.
    d13_algorithm_coverage = sum(
        bool(t.get("algorithm_steps") and t.get("pseudocode"))
        for t in domains["D13"]["techniques"]
    )
    coverage["D13"]["current_manifest_techniques_with_algorithm_and_pseudocode"] = d13_algorithm_coverage
    coverage["D13"]["note"] = (
        "No se encontró point3-complete-algorithms-D13.json. Las fichas D13 "
        "conservan sus algorithm_steps y pseudocode originales, sin atribuirles "
        "una revisión independiente de punto 3."
    )

    # All integrated records remain fail-closed.
    for domain_id in ("D13", "D35", "D36"):
        for technique in domains[domain_id]["techniques"]:
            if "engineering_audit" in technique:
                technique["engineering_audit"]["certification_status"] = "NOT_CERTIFIED"

    execution = read_json(loaded["EXECUTION"])
    source_manifest = {
        "branch": "audit/implementation-ready-manifest",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "audit_files": {
            filename: hashlib.sha256((AUDIT / filename).read_bytes()).hexdigest()
            for filename in FILES.values()
        },
    }

    manifest["manifest"]["version"] = "3.6.0-jedl-studio-engineering-audits-integrated"
    manifest["manifest"]["updated"] = "2026-11-27"
    manifest["manifest"]["status"] = (
        "auditorias_D13_D35_D36_integradas; implementaciones_locales_parciales_con_pruebas; NO_CERTIFICADO"
    )
    manifest["manifest"]["change_summary"] = (
        "42 dominios / 616 técnicas. D13: auditorías dimensionales y derivaciones "
        "integradas por correspondencia nominal, con cobertura parcial explícita. "
        "D35 y D36: 15/15 fichas por dominio con puntos 1–3 y evidencia de punto 4 "
        "e investigación integradas. Se vinculan implementaciones locales y CI "
        "aprobado sin confundir pruebas de referencia con implementación productiva. "
        "El manifiesto completo permanece NO CERTIFICADO."
    )

    manifest["manifest"].setdefault("change_log", [])
    if not any(item.get("version") == "3.6.0" for item in manifest["manifest"]["change_log"]):
        manifest["manifest"]["change_log"].append({
            "version": "3.6.0",
            "change": (
                "Integración en las fichas del manifiesto de auditorías dimensionales "
                "(punto 1), derivaciones justificadas (punto 2), algoritmos/pseudocódigo "
                "(punto 3), validación ejecutable (punto 4) e investigación de "
                "implementaciones reales para D13, D35 y D36. D35/D36 incluyen "
                "implementaciones, pruebas, fuentes y ejecuciones CI enlazadas. "
                "D13 se integra por nombre exacto y declara la ausencia de un informe "
                "independiente de punto 3."
            ),
            "baseline_preserved": (
                "Se preservan las 616 técnicas y los campos originales. Los informes "
                "se incorporan bajo engineering_audit sin sobrescribir ecuaciones, "
                "derivaciones ni pseudocódigo fuente."
            )
        })

    manifest["engineering_audit_integration"] = {
        "title": "Integración de trabajos de ingeniería y auditorías de D13, D35 y D36",
        "integrated_at": "2026-11-27",
        "repository": "juancito860715-lgtm/jedl-studio",
        "source": source_manifest,
        "coverage": coverage,
        "execution_evidence": {
            "workflow": execution.get("workflow"),
            "r31": execution.get("r31"),
            "historical_records": execution.get("historical_records"),
            "manifest_readiness": execution.get("manifest_readiness"),
            "certification": execution.get("certification"),
            "blockers": execution.get("blockers", []),
        },
        "interpretation_rules": [
            "Las auditorías se integran por nombre exacto o record_key verificado; no se reasignan por índice cuando el orden histórico difiere.",
            "Se preservan ecuaciones, derivaciones y pseudocódigo originales; la evidencia añadida vive en engineering_audit.",
            "REFERENCE_TEST_PASSED significa prueba de referencia/oráculo y no se presenta como implementación productiva.",
            "IMPLEMENTED_AND_LOCAL_CI_PASSED y PRODUCTION_IMPLEMENTATION_TEST_PASSED se conservan como evidencia local de implementación y pruebas, no como certificación global.",
            "Todos los registros mantienen NOT_CERTIFIED hasta revisión matemática independiente y validación de runtime aplicable."
        ],
        "global_status": "INTEGRATED_WITH_EXPLICIT_REMAINING_GAPS",
        "remaining_gaps": [
            "D13: la auditoría histórica tiene 16 registros; 15 corresponden por nombre al D13 actual y el registro SDF se reasigna a D02 si existe coincidencia exacta.",
            "D13: no se encontró informe independiente de punto 3; el pseudocódigo existente se conserva sin atribuirle esa revisión.",
            "D13: las técnicas restantes sin auditoría dimensional/derivación adjunta no se marcan como auditadas.",
            "D35/D36: las pruebas de referencia y las implementaciones locales no certifican automáticamente las 30 técnicas ni sustituyen validación completa de navegador/WebGL/WebGPU.",
            "La revisión independiente y la certificación final por técnica continúan pendientes."
        ]
    }

    # Final integrity assertions.
    assert len(manifest["domains"]) == expected_domains
    assert sum(len(item.get("techniques", [])) for item in manifest["domains"]) == expected_techniques
    assert coverage["D35"]["point1"] == coverage["D35"]["point2"] == coverage["D35"]["point3"] == 15
    assert coverage["D36"]["point1"] == coverage["D36"]["point2"] == coverage["D36"]["point3"] == 15
    assert coverage["D35"]["point4"] == coverage["D36"]["point4"] == 15
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Re-open the exact written artifact before returning success.
    check = read_json(MANIFEST)
    assert check["manifest"]["version"] == "3.6.0-jedl-studio-engineering-audits-integrated"
    assert sum(len(item.get("techniques", [])) for item in check["domains"]) == expected_techniques
    print(json.dumps({
        "status": "INTEGRATED",
        "version": check["manifest"]["version"],
        "domains": len(check["domains"]),
        "techniques": sum(len(item.get("techniques", [])) for item in check["domains"]),
        "coverage": coverage,
        "integrated_techniques": sum(
            bool(t.get("engineering_audit"))
            for d in check["domains"] for t in d.get("techniques", [])
        )
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
