#!/usr/bin/env python3
"""Exclude GLB assets that are unsupported or explicitly blocked by project policy."""
from __future__ import annotations

import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNSUPPORTED_EXTENSIONS = {"EXT_meshopt_compression", "KHR_mesh_quantization"}
EXCLUSION_POLICY_PATH = Path("docs/asset_exclusions.json")


class UnsupportedGodotExtensionError(ValueError):
    pass


def read_gltf_document(path: Path) -> dict:
    if path.suffix.lower() == ".gltf":
        value = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".glb":
        payload = path.read_bytes()
        if len(payload) < 20:
            raise ValueError(f"Truncated GLB: {path}")
        magic, version, declared = struct.unpack_from("<4sII", payload, 0)
        if magic != b"glTF" or version != 2 or declared != len(payload):
            raise ValueError(f"Invalid GLB header/version/length: {path}")
        chunk_length, chunk_type = struct.unpack_from("<II", payload, 12)
        if chunk_type != 0x4E4F534A or 20 + chunk_length > len(payload):
            raise ValueError(f"Invalid GLB JSON chunk: {path}")
        value = json.loads(payload[20:20 + chunk_length].decode("utf-8").rstrip(" \t\r\n\x00"))
    else:
        raise ValueError(f"Unsupported model format: {path.suffix}")
    if not isinstance(value, dict) or not isinstance(value.get("asset"), dict):
        raise ValueError(f"Invalid glTF document: {path}")
    return value


def load_exclusion_policy(root: Path) -> dict[str, dict]:
    policy_path = root / EXCLUSION_POLICY_PATH
    if not policy_path.is_file():
        return {}
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("schemaVersion") != 1 or not isinstance(policy.get("exclusions"), list):
        raise ValueError("Invalid docs/asset_exclusions.json policy schema")
    result: dict[str, dict] = {}
    for record in policy["exclusions"]:
        if not isinstance(record, dict):
            raise ValueError("Asset exclusion policy contains an invalid record")
        asset_id = str(record.get("assetId", ""))
        if not asset_id or asset_id in result or record.get("activeCatalogAllowed") is not False:
            raise ValueError(f"Invalid or duplicate explicit asset exclusion: {asset_id}")
        result[asset_id] = record
    return result


def inspect_model(path: Path, asset_id: str) -> dict:
    document = read_gltf_document(path)
    used = sorted(set(document.get("extensionsUsed", [])))
    required = sorted(set(document.get("extensionsRequired", [])))
    incompatible = sorted(UNSUPPORTED_EXTENSIONS.intersection(set(used) | set(required)))
    try:
        display_path = "res://" + path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        display_path = path.name
    return {
        "assetId": asset_id,
        "path": display_path,
        "extensionsUsed": used,
        "extensionsRequired": required,
        "unsupportedGodot441Extensions": incompatible,
        "compatibleByExtensionGate": not incompatible,
    }


def filter_catalog(root: Path = ROOT) -> dict:
    root = root.resolve(strict=True)
    catalog_path = root / "assets/gallery/catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get("assets")
    if not isinstance(entries, list):
        raise ValueError("Catalog assets must be an array")
    extended_root = (root / "assets/gallery/3d/extended").resolve()
    policy_exclusions = load_exclusion_policy(root)
    kept, inspected, excluded = [], [], []
    seen_policy_exclusions: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("kind") != "3d":
            kept.append(entry)
            continue
        resource_path = str(entry.get("path", ""))
        if not resource_path.startswith("res://"):
            raise ValueError(f"Invalid model path for {entry.get('id')}")
        model_path = (root / resource_path[6:]).resolve(strict=True)
        if not model_path.is_relative_to(root) or not model_path.is_file():
            raise ValueError(f"Model path escapes project or is not a file: {resource_path}")
        asset_id = str(entry.get("id", ""))
        record = inspect_model(model_path, asset_id)
        inspected.append(record)
        policy_record = policy_exclusions.get(asset_id)
        if policy_record is not None:
            if not model_path.is_relative_to(extended_root):
                raise ValueError(f"Explicitly excluded asset must remain in extended source area: {asset_id}")
            excluded.append({
                **record,
                "status": "excluded_by_policy",
                "policyReason": str(policy_record.get("reason", "")),
                "reentryCriteria": policy_record.get("reentryCriteria", []),
            })
            seen_policy_exclusions.add(asset_id)
            shutil.rmtree(model_path.parent)
            print(f"GLB_EXCLUDED_BY_POLICY: {asset_id}")
            continue
        if record["compatibleByExtensionGate"]:
            kept.append(entry)
            print(f"GLB_COMPATIBLE: {asset_id} required={record['extensionsRequired']}")
            continue
        if not model_path.is_relative_to(extended_root):
            raise UnsupportedGodotExtensionError(
                f"Core catalog model {asset_id} requires unsupported Godot 4.4.1 extensions: "
                + ", ".join(record["unsupportedGodot441Extensions"])
            )
        excluded.append({
            **record,
            "status": "excluded_unsupported_extension",
            "reason": "Required/used extension is not supported by the audited Godot 4.4.1 importer.",
        })
        shutil.rmtree(model_path.parent)
        print(f"GLB_EXCLUDED_UNSUPPORTED: {asset_id} extensions={record['unsupportedGodot441Extensions']}")

    catalog["assets"] = kept
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    missing_policy_assets = set(policy_exclusions) - seen_policy_exclusions
    report = {
        "schemaVersion": 2,
        "engine": "Godot 4.4.1",
        "unsupportedExtensions": sorted(UNSUPPORTED_EXTENSIONS),
        "inspectedCount": len(inspected),
        "compatibleCount": sum(1 for item in inspected if item["compatibleByExtensionGate"]),
        "excludedCount": len(excluded),
        "activeCatalogCount": len(catalog["assets"]),
        "missingExplicitExclusions": sorted(missing_policy_assets),
        "inspectedAssets": inspected,
        "excludedAssets": excluded,
    }
    if missing_policy_assets:
        raise ValueError("Explicitly excluded assets unexpectedly absent from acquisition/catalog: " + ", ".join(sorted(missing_policy_assets)))
    (root / "assets/gallery/glb_compatibility_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"GLB_COMPATIBILITY_GATE_OK: inspected={report['inspectedCount']} "
        f"compatible={report['compatibleCount']} excluded={report['excludedCount']} "
        f"active={report['activeCatalogCount']}"
    )
    return report


if __name__ == "__main__":
    filter_catalog()
