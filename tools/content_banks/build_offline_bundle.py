#!/usr/bin/env python3
"""Build a single, hash-indexed, installable JEDL offline library package."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

LICENSE = "CC0-1.0"

def safe_path(value: str) -> str:
    p = PurePosixPath(value)
    if not value or p.is_absolute() or "\\" in value or any(x in ("", ".", "..") for x in p.parts):
        raise ValueError(f"Unsafe package path: {value!r}")
    return p.as_posix()

def build(source: Path, output: Path, package_version: str = "1.0.0") -> dict:
    records = []
    for file in sorted(source.rglob("*")):
        if file.is_symlink():
            raise ValueError(f"Symlink not allowed: {file}")
        if not file.is_file() or file.name == "JEDL-PACKAGE.json":
            continue
        relative = safe_path(file.relative_to(source).as_posix())
        raw = file.read_bytes()
        records.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    if not records:
        raise ValueError("Offline package has no payload files")
    community_path = source / "community-2d.zip"
    kenney_catalog_path = source / "kenney" / "catalog.json"
    if not community_path.is_file() or not kenney_catalog_path.is_file():
        raise ValueError("Community and Kenney catalogs are required")
    community_manifest = None
    with zipfile.ZipFile(community_path) as community:
        if "JEDL-PACKAGE.json" not in community.namelist():
            raise ValueError("Community package is missing JEDL-PACKAGE.json")
        community_manifest = json.loads(community.read("JEDL-PACKAGE.json"))
    if community_manifest.get("license") != LICENSE:
        raise ValueError("Community package license is not CC0-1.0")
    kenney_catalog = json.loads(kenney_catalog_path.read_text(encoding="utf-8"))
    if kenney_catalog.get("license") != LICENSE:
        raise ValueError("Kenney catalog license is not CC0-1.0")
    manifest = {
        "schemaVersion": 1,
        "id": "jedl-offline-library",
        "packageVersion": package_version,
        "title": "JEDL Offline Creative Library",
        "license": LICENSE,
        "commercialUse": True,
        "modificationAllowed": True,
        "redistributionAllowed": True,
        "licenseEvidence": [
            "https://creativecommons.org/publicdomain/zero/1.0/",
            "https://kenney.nl/support",
            "https://github.com/Tiddybub/2d-assets"
        ],
        "communityPackCount": community_manifest["packCount"],
        "kenneyPackCount": kenney_catalog["packCount"],
        "files": records,
    }
    payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    (source / "JEDL-PACKAGE.json").write_text(payload, encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.write(source / "JEDL-PACKAGE.json", "JEDL-PACKAGE.json")
        for record in records:
            archive.write(source / record["path"], record["path"])
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(records) + 1
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="build/asset-library")
    parser.add_argument("--out", default="app/src/main/assets/offline_library/jedl-library-bundle.zip")
    args = parser.parse_args()
    manifest = build(Path(args.source), Path(args.out))
    print(f"JEDL_OFFLINE_PACKAGE_OK id={manifest['id']} files={len(manifest['files'])} "
          f"community_packs={manifest['communityPackCount']} kenney_packs={manifest['kenneyPackCount']}")

if __name__ == "__main__":
    main()
