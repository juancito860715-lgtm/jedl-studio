#!/usr/bin/env python3
"""Import a manually mapped CC0 modular-art ZIP into the JEDL style-pack contract.

No computer-vision guesses are made: each source sprite must be explicitly mapped
to a JEDL slot, bone, pivot and design-space size in a reviewed JSON mapping file.
"""
import argparse
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from PIL import Image

RIG_ID = "jedl_humanoid_v1"
RIG_BONES = {
    "torso", "head", "armUL", "foreArmL", "armUR", "foreArmR",
    "thighL", "shinL", "thighR", "shinR"
}
SLOTS = {
    "HEAD", "EYES", "EYEBROWS", "MOUTH", "FACIAL_HAIR", "HAIR_BACK", "HAIR_FRONT",
    "HAT_BACK", "HAT_FRONT", "TORSO", "SHIRT", "PANTS", "UPPER_ARM_L", "UPPER_ARM_R",
    "SLEEVE_L", "SLEEVE_R", "FOREARM_L", "FOREARM_R", "HAND_L", "HAND_R",
    "THIGH_L", "THIGH_R", "SHIN_L", "SHIN_R", "SHOE_L", "SHOE_R"
}
ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}")
REQUIRED_DEFAULT_SLOTS = set(SLOTS)
SLOT_BONES = {
    "HEAD": "head", "EYES": "head", "EYEBROWS": "head", "MOUTH": "head",
    "FACIAL_HAIR": "head", "HAIR_BACK": "head", "HAIR_FRONT": "head",
    "HAT_BACK": "head", "HAT_FRONT": "head",
    "TORSO": "torso", "SHIRT": "torso", "PANTS": "torso",
    "UPPER_ARM_L": "armUL", "SLEEVE_L": "armUL",
    "UPPER_ARM_R": "armUR", "SLEEVE_R": "armUR",
    "FOREARM_L": "foreArmL", "HAND_L": "foreArmL",
    "FOREARM_R": "foreArmR", "HAND_R": "foreArmR",
    "THIGH_L": "thighL", "THIGH_R": "thighR",
    "SHIN_L": "shinL", "SHIN_R": "shinR",
    "SHOE_L": "shinL", "SHOE_R": "shinR"
}


def _safe_source_path(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or "\\" in value or any(p in ("", ".", "..") for p in path.parts):
        raise ValueError(f"Unsafe ZIP source path: {value!r}")
    return path.as_posix()


def _validate_mapping(data):
    if data.get("license") != "CC0-1.0":
        raise ValueError("Only the verified CC0-1.0 candidate is accepted by this importer")
    for key in ("source", "licenseEvidence", "licenseTerms"):
        if not str(data.get(key, "")).startswith("https://"):
            raise ValueError(f"Missing HTTPS license evidence: {key}")
    if data.get("rigId") != RIG_ID or set(data.get("rigBones", [])) != RIG_BONES:
        raise ValueError(f"Pack must declare the complete {RIG_ID} bone contract")
    parts = data.get("parts", [])
    if not parts:
        raise ValueError("Mapping must contain at least one explicitly mapped sprite")
    ids = [p.get("id") for p in parts]
    if any(not isinstance(pid, str) or not ID_RE.fullmatch(pid) for pid in ids):
        raise ValueError("Every part needs a safe, stable ID")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate part IDs")
    by_id = {p["id"]: p for p in parts}
    defaults = data.get("defaults", {})
    if set(defaults) != REQUIRED_DEFAULT_SLOTS:
        raise ValueError("Mapping must provide a default part for every JEDL editor slot")
    if not defaults:
        raise ValueError("Mapping must declare default parts")
    for slot, part_id in defaults.items():
        if slot not in SLOTS or part_id not in by_id or by_id[part_id].get("slot") != slot:
            raise ValueError(f"Invalid default mapping: {slot} -> {part_id}")
    for part in parts:
        if part.get("slot") not in SLOTS or part.get("boneId") != SLOT_BONES.get(part.get("slot")):
            raise ValueError(f"Slot/bone mapping is incompatible for {part.get('id')}")
        for key in ("pivotX", "pivotY"):
            value = part.get(key)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                raise ValueError(f"Invalid normalized pivot {key} for {part['id']}")
        for key in ("widthUnits", "heightUnits"):
            value = part.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"Invalid design-space dimension {key} for {part['id']}")
        if not isinstance(part.get("zIndex"), int):
            raise ValueError(f"Missing integer zIndex for {part['id']}")
        _safe_source_path(part.get("sourceFile", ""))
    return by_id


def import_kenney_pack(zip_path, mapping_path, output_root):
    zip_path, mapping_path, output_root = Path(zip_path), Path(mapping_path), Path(output_root)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    by_id = _validate_mapping(mapping)
    output_root.mkdir(parents=True, exist_ok=True)
    parts_out = []
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for part in mapping["parts"]:
            source_name = _safe_source_path(part["sourceFile"])
            if source_name not in names:
                raise FileNotFoundError(f"Mapped source sprite is absent from ZIP: {source_name}")
            info = archive.getinfo(source_name)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"Symbolic links are not accepted in art ZIPs: {source_name}")
            raw = archive.read(source_name)
            with Image.open(io.BytesIO(raw)) as opened:
                rgba = opened.convert("RGBA")
                if rgba.width < 2 or rgba.height < 2 or rgba.getchannel("A").getbbox() is None:
                    raise ValueError(f"Sprite is empty or invalid: {source_name}")
                file_name = f"characters/{part['id']}.png"
                target = output_root / file_name
                target.parent.mkdir(parents=True, exist_ok=True)
                rgba.save(target, format="PNG", optimize=True)
            item = {k: v for k, v in part.items() if k not in ("sourceFile",)}
            item["file"] = file_name
            item.setdefault("offsetX", 0.0)
            item.setdefault("offsetY", 0.0)
            parts_out.append(item)

    manifest = {
        "id": mapping["id"],
        "version": 1,
        "rigId": RIG_ID,
        "rigBones": sorted(RIG_BONES),
        "parts": parts_out,
        "defaults": mapping["defaults"]
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8"
    )
    source_record = {
        "id": mapping["id"], "title": mapping.get("title", mapping["id"]),
        "publisher": "Kenney", "source": mapping["source"],
        "license": mapping["license"], "licenseEvidence": mapping["licenseEvidence"],
        "licenseTerms": mapping["licenseTerms"],
        "commercialUse": True, "modificationAllowed": True,
        "apkRedistributionAllowed": True, "attributionRequired": False,
        "attributionNote": "Optional courtesy credit: Kenney.nl"
    }
    (output_root / "SOURCE.json").write_text(
        json.dumps(source_record, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8"
    )
    (output_root / "LICENSE.txt").write_text(
        "Kenney Modular Character Pack\\n"
        "License: CC0-1.0 (public domain dedication).\\n"
        "Source listing and license evidence: " + mapping["licenseEvidence"] + "\\n"
        "License terms: " + mapping["licenseTerms"] + "\\n"
        "Attribution to Kenney.nl is appreciated but not required.\\n",
        encoding="utf-8"
    )
    return output_root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, help="Original Kenney ZIP")
    parser.add_argument("--mapping", required=True, help="Reviewed sprite-to-rig mapping JSON")
    parser.add_argument("--out", required=True, help="JEDL style pack output directory")
    args = parser.parse_args()
    result = import_kenney_pack(args.zip, args.mapping, args.out)
    print(f"Imported {len(json.loads((result / 'manifest.json').read_text())['parts'])} mapped sprites into {result}")


if __name__ == "__main__":
    main()
