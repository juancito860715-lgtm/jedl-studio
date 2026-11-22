#!/usr/bin/env python3
"""Fail closed when a downloaded offline asset, preview, license or manifest is invalid."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "assets/gallery/catalog.json"
MANIFEST = ROOT / "assets/gallery/manifest.json"
ALLOWED_LICENSES = {"CC0-1.0", "CC0-1.0 + CC-BY-4.0"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_res_path(root: Path, value: str) -> Path:
    if not value.startswith("res://"):
        raise ValueError(f"Expected res:// path, got: {value}")
    relative = Path(value[6:])
    if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError(f"Unsafe resource path: {value}")
    target = (root / relative).resolve(strict=True)
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Resource escaped project root: {value}")
    if not target.is_file() or target.stat().st_size <= 0:
        raise ValueError(f"Resource is empty or not a file: {value}")
    return target


def _validate_gltf_document(document: dict, model_path: Path) -> None:
    asset = document.get("asset", {})
    if not isinstance(asset, dict) or str(asset.get("version", "")).split(".")[0] != "2":
        raise ValueError(f"Only glTF 2.x assets are accepted: {model_path}")
    for collection in ("buffers", "images"):
        for item in document.get(collection, []):
            uri = item.get("uri", "")
            if not uri or uri.startswith("data:"):
                continue
            parsed = urlparse(uri)
            if parsed.scheme or parsed.netloc:
                raise ValueError(f"External network URI is forbidden in packaged glTF: {uri}")
            rel = Path(uri.replace("\\", "/"))
            if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
                raise ValueError(f"Unsafe glTF dependency path: {uri}")
            dependency = (model_path.parent / rel).resolve(strict=True)
            if not dependency.is_relative_to(model_path.parent.resolve()) or not dependency.is_file():
                raise ValueError(f"Missing or escaped glTF dependency: {uri}")


def validate_model(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix == ".gltf":
        document = json.loads(path.read_text(encoding="utf-8"))
        _validate_gltf_document(document, path)
        return
    if suffix != ".glb":
        raise ValueError(f"3D model must be GLB or glTF, not {suffix}: {path}")
    payload = path.read_bytes()
    if len(payload) < 20:
        raise ValueError(f"GLB is truncated: {path}")
    magic, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(payload):
        raise ValueError(f"GLB header/version/length is invalid: {path}")
    chunk_length, chunk_type = struct.unpack_from("<II", payload, 12)
    if chunk_type != 0x4E4F534A or 20 + chunk_length > len(payload):
        raise ValueError(f"GLB JSON chunk is missing or invalid: {path}")
    document = json.loads(payload[20:20 + chunk_length].decode("utf-8").rstrip(" \t\r\n\x00"))
    _validate_gltf_document(document, path)


def validate_assets(root: Path = ROOT) -> dict:
    catalog_path = root / "assets/gallery/catalog.json"
    manifest_path = root / "assets/gallery/manifest.json"
    if not catalog_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("Generated catalog.json and manifest.json are both required")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if catalog.get("schemaVersion") != 2 or manifest.get("schemaVersion") != 1:
        raise ValueError("Unsupported catalog or root-manifest schema")
    if manifest.get("catalogSha256") != sha256(catalog_path):
        raise ValueError("Catalog SHA-256 differs from root manifest")

    entries = catalog.get("assets")
    manifest_entries = manifest.get("assets")
    if not isinstance(entries, list) or not entries or not isinstance(manifest_entries, list):
        raise ValueError("Catalog and manifest must contain non-empty asset arrays")
    if len(entries) != len(manifest_entries):
        raise ValueError("Catalog and root manifest asset counts differ")

    ids: set[str] = set()
    backgrounds = 0
    models = 0
    for entry in entries:
        asset_id = str(entry.get("id", ""))
        if not asset_id or asset_id in ids:
            raise ValueError(f"Missing or duplicate asset id: {asset_id}")
        ids.add(asset_id)
        kind = entry.get("kind")
        asset_path = resolve_res_path(root, str(entry.get("path", "")))
        license_id = str(entry.get("license", ""))
        if license_id not in ALLOWED_LICENSES:
            raise ValueError(f"License is not approved for {asset_id}: {license_id}")
        evidence = str(entry.get("licenseEvidence", ""))
        source = str(entry.get("source", ""))
        if urlparse(evidence).scheme != "https" or urlparse(source).scheme != "https":
            raise ValueError(f"HTTPS source and license evidence are required: {asset_id}")
        if entry.get("offline") is not True or entry.get("placeable") is not True:
            raise ValueError(f"Asset is not offline/placeable: {asset_id}")
        declared_hash = str(entry.get("sha256", ""))
        if len(declared_hash) != 64 or sha256(asset_path) != declared_hash:
            raise ValueError(f"Downloaded asset SHA-256 mismatch: {asset_id}")

        if kind == "2d":
            backgrounds += 1
            if asset_path.suffix.lower() not in (".jpg", ".jpeg"):
                raise ValueError(f"Only photographic JPEG backplates are allowed in the 2D gallery: {asset_id}")
            if entry.get("category") != "Fondos fotográficos":
                raise ValueError(f"2D assets must be photographic backgrounds only: {asset_id}")
            with Image.open(asset_path) as image:
                image.verify()
            with Image.open(asset_path) as image:
                if image.width < 1024 or image.height < 512:
                    raise ValueError(f"Photographic background resolution is too small: {asset_id}")
        elif kind == "3d":
            models += 1
            validate_model(asset_path)
        else:
            raise ValueError(f"Unsupported catalog kind (2D elements/illustrations are excluded): {kind}")

        preview = str(entry.get("preview_path", ""))
        if preview:
            preview_path = resolve_res_path(root, preview)
            with Image.open(preview_path) as image:
                image.verify()

        license_file = str(entry.get("licenseFile", ""))
        if "CC-BY-4.0" in license_id:
            if not license_file:
                raise ValueError(f"CC-BY asset lacks a packaged license file: {asset_id}")
            license_path = resolve_res_path(root, license_file)
            text = license_path.read_text(encoding="utf-8")
            if "CC-BY-4.0" not in text or "CC0-1.0" not in text:
                raise ValueError(f"Packaged license file does not prove the declared grants: {asset_id}")
            if not str(entry.get("attribution", "")).strip():
                raise ValueError(f"CC-BY asset lacks attribution metadata: {asset_id}")
        elif license_file:
            resolve_res_path(root, license_file)

    if backgrounds == 0 or models == 0:
        raise ValueError("Both photographic backgrounds and 3D models must be present")

    by_id = {str(item.get("assetId", "")): item for item in manifest_entries}
    if set(by_id) != ids:
        raise ValueError("Catalog asset IDs differ from root manifest")
    for entry in entries:
        record = by_id[entry["id"]]
        for field, manifest_field in (("path", "path"), ("sha256", "sha256"), ("license", "license")):
            if str(entry.get(field, "")) != str(record.get(manifest_field, "")):
                raise ValueError(f"Catalog/manifest {field} mismatch for {entry['id']}")

    files = manifest.get("files", [])
    if not isinstance(files, list) or not files:
        raise ValueError("Root manifest has no file inventory")
    for record in files:
        path = resolve_res_path(root, str(record.get("path", "")))
        if path.stat().st_size != int(record.get("sizeBytes", -1)):
            raise ValueError(f"File size differs from root manifest: {record.get('path')}")
        if sha256(path) != str(record.get("sha256", "")):
            raise ValueError(f"File SHA-256 differs from root manifest: {record.get('path')}")
    return {"assets": len(entries), "photographic_backgrounds": backgrounds, "models_3d": models, "files": len(files)}


def main() -> None:
    result = validate_assets()
    print("ASSET_DOWNLOAD_VALIDATION_OK: " + " ".join(f"{key}={value}" for key, value in result.items()))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ASSET_DOWNLOAD_VALIDATION_FAILED: {error}", file=sys.stderr)
        raise
