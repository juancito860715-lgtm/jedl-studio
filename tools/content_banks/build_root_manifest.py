#!/usr/bin/env python3
"""Build a deterministic root manifest for the offline Godot asset catalog."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_CATALOG = "assets/gallery/catalog.json"
DEFAULT_OUTPUT = "assets/gallery/manifest.json"
ASSET_ROOTS = ("assets/gallery", "assets/characters")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_res_path(root: Path, resource_path: str) -> Path:
    if not isinstance(resource_path, str) or not resource_path.startswith("res://"):
        raise ValueError(f"Asset path must use res://: {resource_path!r}")
    raw = resource_path[6:]
    if not raw or raw.startswith("/") or "\\" in raw:
        raise ValueError(f"Unsafe asset path: {resource_path}")
    parts = raw.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Unsafe asset path: {resource_path}")
    candidate = (root / Path(*parts)).resolve(strict=True)
    if not candidate.is_file() or not candidate.is_relative_to(root):
        raise ValueError(f"Asset path does not resolve to a file inside the project: {resource_path}")
    return candidate


def build_manifest(
    root: Path,
    catalog_relative_path: str = DEFAULT_CATALOG,
    output_relative_path: str = DEFAULT_OUTPUT,
) -> dict:
    root = root.resolve(strict=True)
    catalog_path = (root / catalog_relative_path).resolve(strict=True)
    if not catalog_path.is_relative_to(root) or not catalog_path.is_file():
        raise ValueError("Catalog must be a file inside the project root")
    output_path = root / output_relative_path
    if not output_path.resolve(strict=False).is_relative_to(root):
        raise ValueError("Manifest output must remain inside the project root")

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read catalog JSON: {error}") from error
    if not isinstance(catalog, dict) or catalog.get("schemaVersion") != 2:
        raise ValueError("Catalog schemaVersion must be 2")
    catalog_id = catalog.get("catalogId")
    entries = catalog.get("assets")
    if not isinstance(catalog_id, str) or not catalog_id.strip():
        raise ValueError("Catalog requires a non-empty catalogId")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Catalog requires a non-empty assets array")

    policy = catalog.get("licensePolicy", {})
    allowed_licenses = policy.get("allowed", []) if isinstance(policy, dict) else []
    if not isinstance(allowed_licenses, list) or not allowed_licenses:
        raise ValueError("Catalog licensePolicy must list allowed licenses")

    seen_ids: set[str] = set()
    manifest_assets: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every catalog asset must be an object")
        asset_id = entry.get("id")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ValueError("Every catalog asset requires a non-empty id")
        if asset_id in seen_ids:
            raise ValueError(f"Duplicate asset id: {asset_id}")
        seen_ids.add(asset_id)
        if entry.get("kind") not in ("2d", "3d"):
            raise ValueError(f"Unsupported asset kind for {asset_id}")
        license_id = entry.get("license")
        if not isinstance(license_id, str) or not license_id.strip():
            raise ValueError(f"Missing license evidence for {asset_id}")
        declared_licenses = [item.strip() for item in license_id.split("+")]
        if any(item not in allowed_licenses for item in declared_licenses):
            raise ValueError(f"License is not allowed by catalog policy for {asset_id}: {license_id}")
        if entry.get("offline") is not True or entry.get("placeable") is not True:
            raise ValueError(f"Asset must be offline and placeable: {asset_id}")

        asset_file = resolve_res_path(root, entry.get("path", ""))
        actual_hash = sha256_file(asset_file)
        declared_hash = entry.get("sha256")
        if declared_hash and declared_hash != actual_hash:
            raise ValueError(f"SHA-256 mismatch for {asset_id}")
        entry["sha256"] = actual_hash

        preview_path = entry.get("preview_path", "")
        if preview_path:
            resolve_res_path(root, preview_path)
        manifest_assets.append({
            "assetId": asset_id,
            "kind": entry["kind"],
            "category": str(entry.get("category", "")),
            "path": entry["path"],
            "previewPath": preview_path,
            "license": license_id,
            "source": str(entry.get("source", "")),
            "publisher": str(entry.get("publisher", "")),
            "authors": entry.get("authors", {}),
            "sha256": actual_hash,
            "offline": True,
            "placeable": True,
        })

    # Persist computed hashes back into the catalog so the app and root manifest
    # share one canonical asset identity and digest.
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    excluded = output_path.resolve(strict=False)
    files: list[dict] = []
    for relative_root in ASSET_ROOTS:
        folder = root / relative_root
        if not folder.exists():
            continue
        if folder.is_symlink():
            raise ValueError(f"Asset directory cannot be a symlink: {relative_root}")
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Asset package contains a symlink: {path}")
            if not path.is_file() or path.resolve() == excluded:
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError(f"Asset escaped project root: {path}")
            files.append({
                "path": "res://" + path.relative_to(root).as_posix(),
                "sizeBytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    if not files:
        raise ValueError("No offline asset files were found")

    catalog_hash = sha256_file(catalog_path)
    total_bytes = sum(item["sizeBytes"] for item in files)
    manifest = {
        "schemaVersion": 1,
        "packageId": "jedl_studio_offline_assets_v1",
        "version": 1,
        "catalogId": catalog_id,
        "catalogPath": "res://" + catalog_path.relative_to(root).as_posix(),
        "catalogSha256": catalog_hash,
        "assetCount": len(manifest_assets),
        "assets": manifest_assets,
        "fileCount": len(files),
        "totalBytes": total_bytes,
        "files": files,
        "licensePolicy": catalog.get("licensePolicy", {}),
        "attribution": str(catalog.get("attribution", "")),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--out", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(args.root, args.catalog, args.out)
    print(
        "ROOT_MANIFEST_OK: "
        f"assets={manifest['assetCount']} files={manifest['fileCount']} "
        f"bytes={manifest['totalBytes']} catalog_sha256={manifest['catalogSha256']}"
    )


if __name__ == "__main__":
    main()
