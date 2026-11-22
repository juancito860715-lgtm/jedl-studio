#!/usr/bin/env python3
"""Verify that Godot's per-resource import/instance/renderability report is complete and clean."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "assets/gallery/catalog.json"
MANIFEST = ROOT / "assets/gallery/manifest.json"
REPORT = ROOT / "assets/gallery/validation_report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_report(root: Path = ROOT) -> dict:
    catalog_path = root / "assets/gallery/catalog.json"
    manifest_path = root / "assets/gallery/manifest.json"
    report_path = root / "assets/gallery/validation_report.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schemaVersion") != 1:
        raise ValueError("Unsupported Godot validation report schema")
    if report.get("catalogSha256") != sha256(catalog_path):
        raise ValueError("Godot validation report does not match the current catalog hash")
    entries = catalog.get("assets", [])
    records = report.get("assets", [])
    if not isinstance(entries, list) or not isinstance(records, list):
        raise ValueError("Catalog/report assets must be arrays")
    expected_ids = {str(item.get("id", "")) for item in entries}
    record_ids = [str(item.get("assetId", "")) for item in records]
    if len(record_ids) != len(set(record_ids)) or set(record_ids) != expected_ids:
        raise ValueError("Godot report asset IDs differ from the active catalog")
    by_id = {str(item["assetId"]): item for item in records}
    for asset_id in sorted(expected_ids):
        record = by_id[asset_id]
        if not all(record.get(key) is True for key in ("importado", "instanciado", "renderizable")):
            raise ValueError(f"Godot validation failed for {asset_id}: {record}")
        if record.get("errors"):
            raise ValueError(f"Godot validation reported errors for {asset_id}: {record['errors']}")
    manifest_files = {str(item.get("path", "")): item for item in manifest.get("files", [])}
    report_record = manifest_files.get("res://assets/gallery/validation_report.json")
    if not report_record:
        raise ValueError("Root manifest does not include validation_report.json")
    if report_record.get("sha256") != sha256(report_path):
        raise ValueError("Validation report hash differs from root manifest")
    if report_record.get("sizeBytes") != report_path.stat().st_size:
        raise ValueError("Validation report size differs from root manifest")
    return {"assets": len(records), "imported": len(records), "instantiated": len(records), "renderable": len(records)}


if __name__ == "__main__":
    result = validate_report()
    print("CATALOG_REPORT_VALIDATION_OK: " + " ".join(f"{key}={value}" for key, value in result.items()))
