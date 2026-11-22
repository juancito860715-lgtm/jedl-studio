#!/usr/bin/env python3
"""Fail if Godot did not create import sidecars and cached outputs for catalog assets."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

IMPORTABLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gltf", ".glb"}
IMPORT_OUTPUT_LINE = re.compile(
    r'^\s*(path(?:\.[A-Za-z0-9_]+)?|dest_files)\s*=\s*(.*?)\s*$',
    re.MULTILINE,
)
RES_PATH = re.compile(r'"res://([^"]+)"')


def imported_cache_paths(sidecar_text: str) -> list[str]:
    """Read Godot 4.x remap paths and [deps] dest_files entries."""
    paths: list[str] = []
    for match in IMPORT_OUTPUT_LINE.finditer(sidecar_text):
        _key, value = match.groups()
        paths.extend(RES_PATH.findall(value))
    return list(dict.fromkeys(paths))


def verify_import_artifacts(root: Path, manifest_path: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    manifest_path = manifest_path or root / "assets/gallery/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Root manifest has no file inventory")

    expected = []
    for record in files:
        if not isinstance(record, dict):
            raise ValueError("Root manifest contains an invalid file record")
        resource_path = str(record.get("path", ""))
        if not resource_path.startswith("res://"):
            raise ValueError(f"Invalid resource path in root manifest: {resource_path}")
        if Path(resource_path).suffix.lower() in IMPORTABLE_EXTENSIONS:
            expected.append(resource_path)
    if not expected:
        raise ValueError("No importable JPG/PNG/GLTF/GLB assets were found in root manifest")

    imported_dir = (root / ".godot/imported").resolve(strict=False)
    missing_sidecars: list[str] = []
    missing_cache: list[str] = []
    checked = 0

    for resource_path in expected:
        source = root / resource_path[6:]
        if not source.is_file() or source.stat().st_size <= 0:
            raise ValueError(f"Manifest import source is missing or empty: {resource_path}")
        sidecar = Path(str(source) + ".import")
        if not sidecar.is_file() or sidecar.stat().st_size <= 0:
            missing_sidecars.append(resource_path)
            continue

        matches = imported_cache_paths(sidecar.read_text(encoding="utf-8", errors="replace"))
        if not matches:
            missing_cache.append(resource_path + " (no imported cache path in .import)")
            continue

        invalid_outputs: list[str] = []
        for declared in matches:
            relative_path = Path(declared)
            if relative_path.is_absolute() or any(part in ("", ".", "..") for part in relative_path.parts):
                invalid_outputs.append(f"{declared} (unsafe path)")
                continue
            cache_path = (root / relative_path).resolve(strict=False)
            if not cache_path.is_relative_to(imported_dir):
                invalid_outputs.append(f"{declared} (outside .godot/imported)")
            elif not cache_path.is_file():
                invalid_outputs.append(f"{declared} (file missing)")
            elif cache_path.stat().st_size <= 0:
                invalid_outputs.append(f"{declared} (file empty)")

        if invalid_outputs:
            missing_cache.append(resource_path + " [" + ", ".join(invalid_outputs) + "]")
            continue
        checked += 1

    if missing_sidecars or missing_cache:
        details = []
        if missing_sidecars:
            details.append("missing .import sidecars: " + ", ".join(missing_sidecars[:20]))
        if missing_cache:
            details.append("missing .godot/imported cache outputs: " + ", ".join(missing_cache[:20]))
        raise ValueError("; ".join(details))

    if not imported_dir.is_dir():
        raise ValueError("Godot did not create .godot/imported/")
    cache_files = [path for path in imported_dir.rglob("*") if path.is_file() and path.stat().st_size > 0]
    if not cache_files:
        raise ValueError(".godot/imported/ contains no non-empty imported resources")
    return {
        "expectedImportableResources": len(expected),
        "verifiedSidecarsAndCache": checked,
        "importSidecarCount": sum(1 for item in expected if (root / (item[6:] + ".import")).is_file()),
        "cacheFileCount": len(cache_files),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = verify_import_artifacts(args.root, args.manifest)
    print("GODOT_IMPORT_ARTIFACTS_OK: " + " ".join(f"{key}={value}" for key, value in result.items()))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"GODOT_IMPORT_ARTIFACTS_FAILED: {error}", file=sys.stderr)
        raise
