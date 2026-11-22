#!/usr/bin/env python3
"""Verify Godot's complete per-resource integrity/import/instance/renderability report."""
from __future__ import annotations

import hashlib
import json
import os
import re
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


def engine_versions_match(cli_version: str, report_engine: str) -> bool:
    """Match CLI's truncated hash to Engine's complete official build hash."""
    cli_match = re.fullmatch(
        r"(\d+\.\d+\.\d+\.stable\.official\.)([0-9a-f]{9,40})",
        cli_version.strip(),
    )
    report_match = re.fullmatch(
        r"Godot (\d+\.\d+\.\d+\.stable\.official\.)([0-9a-f]{9,40})",
        report_engine.strip(),
    )
    return bool(
        cli_match
        and report_match
        and cli_match.group(1) == report_match.group(1)
        and report_match.group(2).startswith(cli_match.group(2))
    )


def validate_report(root: Path = ROOT) -> dict:
    catalog_path = root / "assets/gallery/catalog.json"
    manifest_path = root / "assets/gallery/manifest.json"
    report_path = root / "assets/gallery/validation_report.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("schemaVersion") != 2:
        raise ValueError("Unsupported Godot validation report schema")
    expected_version = os.environ.get("GODOT_VERSION", "").strip()
    if not expected_version:
        raise ValueError("GODOT_VERSION is not set to the pinned Godot executable version")
    expected_engine = f"Godot {expected_version}"
    reported_engine = str(report.get("engine", ""))
    if not engine_versions_match(expected_version, reported_engine):
        raise ValueError(
            f"Godot validation report engine mismatch: expected CLI version {expected_engine!r}, "
            f"got runtime version {reported_engine!r}"
        )
    if report.get("catalogSha256") != sha256(catalog_path):
        raise ValueError("Godot validation report does not match the current catalog hash")
    entries = catalog.get("assets", [])
    manifest_assets = manifest.get("assets", [])
    records = report.get("assets", [])
    if not all(isinstance(value, list) for value in (entries, manifest_assets, records)):
        raise ValueError("Catalog, manifest and report assets must be arrays")
    expected_ids = {str(item.get("id", "")) for item in entries}
    manifest_by_id = {str(item.get("assetId", "")): item for item in manifest_assets}
    record_ids = [str(item.get("assetId", "")) for item in records]
    if len(record_ids) != len(set(record_ids)) or set(record_ids) != expected_ids:
        raise ValueError("Godot report asset IDs differ from the active catalog")
    if set(manifest_by_id) != expected_ids:
        raise ValueError("Root manifest asset IDs differ from the active catalog")
    manifest_files = {str(item.get("path", "")): item for item in manifest.get("files", [])}
    by_id = {str(item["assetId"]): item for item in records}
    for asset_id in sorted(expected_ids):
        record = by_id[asset_id]
        manifest_asset = manifest_by_id[asset_id]
        if not all(record.get(key) is True for key in (
            "importado", "instanciado", "renderizable", "dependenciesValid"
        )):
            raise ValueError(f"Godot validation failed for {asset_id}: {record}")
        if record.get("errors"):
            raise ValueError(f"Godot validation reported errors for {asset_id}: {record['errors']}")
        if record.get("assetSha256") != manifest_asset.get("sha256"):
            raise ValueError(f"Godot asset SHA-256 differs from manifest for {asset_id}")
        if int(record.get("assetSizeBytes", -1)) != int(manifest_asset.get("sizeBytes", -2)):
            raise ValueError(f"Godot asset size differs from manifest for {asset_id}")
        dependencies = manifest_asset.get("dependencies", [])
        if sorted(record.get("dependencies", [])) != sorted(dependencies):
            raise ValueError(f"Godot dependency list differs from manifest for {asset_id}")
        for dependency in dependencies:
            if dependency not in manifest_files:
                raise ValueError(f"Model dependency is missing from manifest file inventory: {asset_id} -> {dependency}")
        if manifest_asset.get("kind") == "3d" and int(record.get("nodeCount", 0)) <= 0:
            raise ValueError(f"3D scene has zero child nodes: {asset_id}")
        if manifest_asset.get("kind") == "3d" and (
            int(record.get("meshInstances", 0)) <= 0 or int(record.get("surfaces", 0)) <= 0
        ):
            raise ValueError(f"3D scene has no renderable mesh surfaces: {asset_id}")

    report_record = manifest_files.get("res://assets/gallery/validation_report.json")
    if not report_record:
        raise ValueError("Root manifest does not include validation_report.json")
    if report_record.get("sha256") != sha256(report_path):
        raise ValueError("Validation report hash differs from root manifest")
    if report_record.get("sizeBytes") != report_path.stat().st_size:
        raise ValueError("Validation report size differs from root manifest")
    return {
        "assets": len(records),
        "imported": len(records),
        "instantiated": len(records),
        "renderable": len(records),
        "dependenciesVerified": sum(len(item.get("dependencies", [])) for item in records),
        "threeDimensionalNodeCountsVerified": sum(1 for item in manifest_assets if item.get("kind") == "3d"),
    }


if __name__ == "__main__":
    result = validate_report()
    print("CATALOG_REPORT_VALIDATION_OK: " + " ".join(f"{key}={value}" for key, value in result.items()))
