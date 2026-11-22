#!/usr/bin/env python3
"""Exclude extended GLB assets whose required compression extensions fail Godot 4.4.1 import."""
from __future__ import annotations
import json
import shutil
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNSUPPORTED_EXTENSIONS = {"EXT_meshopt_compression", "KHR_mesh_quantization"}

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
        "assetId": asset_id, "path": display_path,
        "extensionsUsed": used, "extensionsRequired": required,
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
    kept, inspected, excluded = [], [], []
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
        record = inspect_model(model_path, str(entry.get("id", "")))
        inspected.append(record)
        if record["compatibleByExtensionGate"]:
            kept.append(entry)
            print(f"GLB_COMPATIBLE: {record['assetId']} required={record['extensionsRequired']}")
            continue
        if not model_path.is_relative_to(extended_root):
            raise UnsupportedGodotExtensionError(
                f"Core catalog model {record['assetId']} requires unsupported Godot 4.4.1 extensions: "
                + ", ".join(record["unsupportedGodot441Extensions"])
            )
        folder = model_path.parent
        excluded.append({
            **record, "status": "excluded",
            "reason": "Required/used extension is not supported by the audited Godot 4.4.1 importer.",
        })
        if folder.is_relative_to(extended_root):
            shutil.rmtree(folder)
        print(f"GLB_EXCLUDED_UNSUPPORTED: {record['assetId']} extensions={record['unsupportedGodot441Extensions']}")
    catalog["assets"] = kept
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "schemaVersion": 1, "engine": "Godot 4.4.1",
        "unsupportedExtensions": sorted(UNSUPPORTED_EXTENSIONS),
        "inspectedCount": len(inspected),
        "compatibleCount": sum(1 for item in inspected if item["compatibleByExtensionGate"]),
        "excludedCount": len(excluded),
        "inspectedAssets": inspected, "excludedAssets": excluded,
    }
    (root / "assets/gallery/glb_compatibility_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"GLB_COMPATIBILITY_GATE_OK: inspected={report['inspectedCount']} compatible={report['compatibleCount']} excluded={report['excludedCount']}")
    return report

if __name__ == "__main__":
    filter_catalog()
