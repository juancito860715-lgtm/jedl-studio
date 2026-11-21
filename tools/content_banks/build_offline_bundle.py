#!/usr/bin/env python3
"""Build a compact installable CC0 package from approved PNG banks and community assets."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

LICENSE = "CC0-1.0"
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
REQUIRED_BANK_IDS = {
    "kenney_modular_character_pack",
    "kenney_tiny_town_objects",
    "kenney_foliage_objects",
    "jedl_original_instruments_v1",
    "jedl_original_clothing_v1",
}

def safe_path(value: str) -> str:
    p = PurePosixPath(value)
    if (not value or p.is_absolute() or "\\" in value or
            any(x in ("", ".", "..") for x in value.split("/"))):
        raise ValueError(f"Unsafe package path: {value!r}")
    return p.as_posix()

def verify_community(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None or "JEDL-PACKAGE.json" not in archive.namelist():
            raise ValueError("Community package is corrupt or missing its root manifest")
        manifest = json.loads(archive.read("JEDL-PACKAGE.json"))
        if manifest.get("license") != LICENSE:
            raise ValueError("Community package license is not CC0-1.0")
        packs = manifest.get("packs", [])
        records = manifest.get("files", [])
        if not packs or not records:
            raise ValueError("Community package has no verified packs or file inventory")
        names = set(archive.namelist())
        pack_ids = set()
        for pack in packs:
            pack_id = pack.get("pack", "")
            evidence = safe_path(pack.get("sourceEvidenceFile", ""))
            source_url = pack.get("sourceUrl", "")
            if (not pack_id or pack_id in pack_ids or
                    "CC0" not in pack.get("sourceLicenseStatement", "").upper() or
                    not source_url.startswith("https://") or evidence not in names or
                    not evidence.endswith(pack_id + "/SOURCE.md")):
                raise ValueError("Community pack is missing CC0 source evidence")
            evidence_text = archive.read(evidence).decode("utf-8", errors="replace")
            if "CC0" not in evidence_text.upper() or source_url not in evidence_text:
                raise ValueError("Community SOURCE.md does not substantiate its CC0 declaration")
            pack_ids.add(pack_id)
        seen = set()
        for item in records:
            relative = safe_path(item["path"])
            if relative in seen:
                raise ValueError("Duplicate community path: " + relative)
            seen.add(relative)
            raw = archive.read(relative)
            if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("Community file hash mismatch")
        if seen != names - {"JEDL-PACKAGE.json"}:
            raise ValueError("Community manifest inventory does not match archive entries")
        return len(packs)

def verify_banks(source: Path) -> list:
    banks_root = source / "banks"
    if not banks_root.is_dir():
        raise ValueError("Offline package has no banks/ directory")
    manifests = sorted(banks_root.rglob("manifest.json"))
    if not manifests:
        raise ValueError("Offline package has no installable PNG banks")
    result = []
    seen_ids = set()
    for manifest_path in manifests:
        bank_root = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        bank_id = manifest.get("id", "")
        if not bank_id or bank_id in seen_ids:
            raise ValueError("Missing or duplicate bank ID")
        seen_ids.add(bank_id)
        if (manifest.get("license") != LICENSE or not manifest.get("commercialUse") or
                not manifest.get("modificationAllowed") or not manifest.get("apkRedistributionAllowed") or
                not manifest.get("source", "").startswith("https://") or
                not manifest.get("licenseTerms", "").startswith(CC0_URL)):
            raise ValueError("Bank license or redistribution contract is incomplete: " + bank_id)
        if not (bank_root / "LICENSE.txt").is_file() or not (bank_root / "SOURCE.json").is_file():
            raise ValueError("Bank license evidence files are missing: " + bank_id)
        license_text = (bank_root / "LICENSE.txt").read_text(encoding="utf-8", errors="replace")
        source_evidence = json.loads((bank_root / "SOURCE.json").read_text(encoding="utf-8"))
        if ("CC0" not in license_text.upper() or source_evidence.get("license") != LICENSE or
                source_evidence.get("source") != manifest.get("source")):
            raise ValueError("Bank evidence files do not match the CC0 manifest: " + bank_id)
        assets = manifest.get("assets", [])
        if not assets or len(assets) != manifest.get("assetCount"):
            raise ValueError("Bank asset count does not match manifest: " + bank_id)
        for item in assets:
            relative = safe_path(item["file"])
            if not relative.startswith("png/") or not relative.lower().endswith(".png"):
                raise ValueError("Only PNG scene assets are installable: " + bank_id)
            file = bank_root / relative
            raw = file.read_bytes()
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("Bank asset hash mismatch: " + bank_id)
        result.append({
            "id": bank_id,
            "title": manifest.get("title", bank_id),
            "license": LICENSE,
            "assetCount": len(assets),
            "source": manifest["source"],
        })
    missing = REQUIRED_BANK_IDS - seen_ids
    if missing:
        raise ValueError("Offline package is missing required scene banks: " + ", ".join(sorted(missing)))
    return result

def build(source: Path, output: Path, package_version: str = "1.0.0") -> dict:
    source = Path(source)
    community_path = source / "community-2d.zip"
    if not community_path.is_file():
        raise ValueError("Community CC0 package is required")
    community_count = verify_community(community_path)
    banks = verify_banks(source)

    records = []
    for file in sorted(source.rglob("*")):
        if file.is_symlink():
            raise ValueError(f"Symlink not allowed: {file}")
        if not file.is_file() or file.name == "JEDL-PACKAGE.json":
            continue
        relative = safe_path(file.relative_to(source).as_posix())
        if relative.startswith("kenney/"):
            raise ValueError("Raw source archives are not part of the installable scene library")
        raw = file.read_bytes()
        records.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    if not records:
        raise ValueError("Offline package has no payload files")

    manifest = {
        "schemaVersion": 1,
        "id": "jedl-offline-library",
        "packageVersion": package_version,
        "title": "JEDL Offline Creative Library",
        "license": LICENSE,
        "commercialUse": True,
        "modificationAllowed": True,
        "redistributionAllowed": True,
        "licenseEvidence": [CC0_URL, "https://github.com/Tiddybub/2d-assets",
                            "https://github.com/juancito860715-lgtm/jedl-studio"],
        "communityPackCount": community_count,
        "bankCount": len(banks),
        "banks": banks,
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
        if archive.testzip() is not None or len(archive.namelist()) != len(records) + 1:
            raise ValueError("Offline package ZIP verification failed")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="build/asset-library")
    parser.add_argument("--out", default="app/src/main/assets/offline_library/jedl-library-bundle.zip")
    args = parser.parse_args()
    manifest = build(Path(args.source), Path(args.out))
    print(f"JEDL_OFFLINE_PACKAGE_OK id={manifest['id']} files={len(manifest['files'])} "
          f"community_packs={manifest['communityPackCount']} banks={manifest['bankCount']}")

if __name__ == "__main__":
    main()
