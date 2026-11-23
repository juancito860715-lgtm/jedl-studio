#!/usr/bin/env python3
"""Verify the checked-in starter catalog, transparent PNGs and SHA-256 manifest offline."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "assets/gallery/catalog.json"
MANIFEST_PATH = ROOT / "assets/gallery/manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_info(path: Path) -> tuple[int, int, bool]:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Invalid PNG: {path}")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    if width <= 0 or height <= 0 or bit_depth not in (8, 16):
        raise ValueError(f"Invalid PNG dimensions/bit depth: {path}")
    return width, height, color_type in (4, 6)


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if catalog.get("schemaVersion") != 2 or manifest.get("schemaVersion") != 1:
        raise AssertionError("Unsupported catalog or manifest schema")
    if manifest.get("catalogSha256") != sha256(CATALOG_PATH):
        raise AssertionError("Catalog SHA-256 mismatch")
    entries = catalog.get("assets", [])
    manifest_assets = {item["assetId"]: item for item in manifest.get("assets", [])}
    if len(entries) != len(manifest_assets):
        raise AssertionError("Catalog/manifest asset count mismatch")
    seen = set()
    kinds = {"2d": 0, "3d": 0}
    for entry in entries:
        asset_id = entry["id"]
        if asset_id in seen:
            raise AssertionError(f"Duplicate asset ID: {asset_id}")
        seen.add(asset_id)
        if entry.get("license") != "CC0-1.0" or entry.get("offline") is not True or entry.get("placeable") is not True:
            raise AssertionError(f"License/offline/placeable metadata invalid: {asset_id}")
        path = ROOT / entry["path"].removeprefix("res://")
        if not path.is_file() or path.stat().st_size <= 0:
            raise AssertionError(f"Missing/empty local asset: {asset_id}")
        digest = sha256(path)
        if entry.get("sha256") != digest:
            raise AssertionError(f"Asset SHA-256 mismatch: {asset_id}")
        record = manifest_assets.get(asset_id, {})
        if record.get("path") != entry["path"] or record.get("sha256") != digest or record.get("license") != "CC0-1.0":
            raise AssertionError(f"Manifest record mismatch: {asset_id}")
        kinds[entry["kind"]] += 1
        if entry["kind"] == "2d":
            if path.suffix.lower() != ".png" or not png_info(path)[2]:
                raise AssertionError(f"2D sprite must be a transparent PNG: {asset_id}")
    for item in manifest.get("files", []):
        path = ROOT / item["path"].removeprefix("res://")
        if not path.is_file() or path.stat().st_size != item["sizeBytes"] or sha256(path) != item["sha256"]:
            raise AssertionError(f"Manifest file integrity failure: {item['path']}")
    if kinds["2d"] < 1 or kinds["3d"] < 1:
        raise AssertionError("Starter catalog must contain at least one 2D and one 3D asset")
    print(f"LOCAL_CATALOG_OK assets={len(entries)} 2d={kinds['2d']} 3d={kinds['3d']} bytes={manifest['totalBytes']}")


if __name__ == "__main__":
    main()
