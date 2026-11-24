#!/usr/bin/env python3
"""Validate a local CC0 PNG character bank against the JEDL humanoid rig."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import zlib
from pathlib import Path
from urllib.parse import urlparse

BANK_ROOT = "assets/characters/banks"
RIG_ID = "jedl_humanoid_v1"
RIG_SCHEMA_VERSION = 1
ALLOWED_LICENSE = "CC0-1.0"
CC0_EVIDENCE = "https://creativecommons.org/publicdomain/zero/1.0/"
SLOTS = ("head", "torso", "arm_left", "arm_right", "leg_left", "leg_right")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PARTS = 64
MAX_TEXTURE_DIMENSION = 1024
MAX_TEXTURE_PIXELS = 1024 * 1024
MAX_PART_BYTES = 4 * 1024 * 1024
MAX_BANK_BYTES = 24 * 1024 * 1024
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_BANK_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")


class BankValidationError(ValueError):
    """Raised when a character bank is unsafe or incompatible with the rig."""


def _fail(message: str) -> None:
    raise BankValidationError(message)


def _non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"{label} must be a non-empty string")
    return value.strip()


def _is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def _reject_symlink_components(root: Path, candidate: Path) -> None:
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        _fail(f"Path escapes project root: {candidate}")
    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            _fail(f"Symlink is not allowed in character bank: {current}")


def _resolve_bank_file(root: Path, raw_path: object, bank_dir: Path, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.startswith("res://"):
        _fail(f"{label} must use a local res:// path")
    relative = raw_path[6:]
    if not relative or relative.startswith("/") or "\\" in relative:
        _fail(f"Unsafe {label}: {raw_path!r}")
    components = relative.split("/")
    if any(component in ("", ".", "..") for component in components):
        _fail(f"Unsafe {label}: {raw_path!r}")
    expected_prefix = bank_dir.relative_to(root).as_posix() + "/"
    if not relative.startswith(expected_prefix):
        _fail(f"{label} must remain inside this bank directory")
    candidate = root.joinpath(*components)
    _reject_symlink_components(root, candidate)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        _fail(f"{label} does not exist: {raw_path} ({error})")
    if not resolved.is_file() or not resolved.is_relative_to(bank_dir):
        _fail(f"{label} must resolve to a regular file inside this bank: {raw_path}")
    return resolved


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 45 or data[:8] != PNG_SIGNATURE:
        _fail(f"Invalid PNG signature or truncated file: {path}")
    offset = 8
    width = height = 0
    saw_ihdr = False
    saw_idat = False
    saw_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            _fail(f"Truncated PNG chunk: {path}")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            _fail(f"PNG chunk exceeds file size: {path}")
        payload = data[payload_start:payload_end]
        declared_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if declared_crc != actual_crc:
            _fail(f"PNG CRC mismatch: {path}")
        if not saw_ihdr:
            if kind != b"IHDR" or length != 13:
                _fail(f"PNG must begin with a valid IHDR chunk: {path}")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if width <= 0 or height <= 0:
                _fail(f"PNG dimensions must be positive: {path}")
            if bit_depth != 8 or color_type not in (4, 6):
                _fail(f"Character PNG must be 8-bit with an alpha channel: {path}")
            if compression != 0 or filter_method != 0 or interlace not in (0, 1):
                _fail(f"Unsupported PNG encoding: {path}")
            if width > MAX_TEXTURE_DIMENSION or height > MAX_TEXTURE_DIMENSION:
                _fail(f"PNG dimension exceeds {MAX_TEXTURE_DIMENSION}px: {path}")
            if width * height > MAX_TEXTURE_PIXELS:
                _fail(f"PNG pixel count exceeds mobile budget: {path}")
            saw_ihdr = True
        elif kind == b"IHDR":
            _fail(f"PNG contains multiple IHDR chunks: {path}")
        if kind == b"IDAT":
            saw_idat = True
        if kind == b"IEND":
            if length != 0:
                _fail(f"PNG IEND chunk must be empty: {path}")
            saw_iend = True
            offset = crc_end
            if offset != len(data):
                _fail(f"PNG contains data after IEND: {path}")
            break
        offset = crc_end
    if not saw_ihdr or not saw_idat or not saw_iend:
        _fail(f"PNG is missing IHDR, IDAT or IEND: {path}")
    return width, height


def validate_bank(root: Path, manifest_path: Path) -> dict:
    root = Path(root).resolve(strict=True)
    candidate_manifest = Path(manifest_path)
    if not candidate_manifest.is_absolute():
        candidate_manifest = root / candidate_manifest
    try:
        manifest_resolved = candidate_manifest.resolve(strict=True)
    except OSError as error:
        _fail(f"Character bank manifest does not exist: {candidate_manifest} ({error})")
    if not manifest_resolved.is_relative_to(root) or not manifest_resolved.is_file():
        _fail("Character bank manifest must be a regular file inside the project")
    _reject_symlink_components(root, candidate_manifest)

    try:
        manifest = json.loads(manifest_resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        _fail(f"Cannot read character bank manifest: {error}")
    if not isinstance(manifest, dict):
        _fail("Character bank manifest root must be an object")
    if manifest.get("schemaVersion") != 1:
        _fail("schemaVersion must be 1")

    bank_id = _non_empty_string(manifest.get("bankId"), "bankId")
    if not _BANK_PATTERN.fullmatch(bank_id):
        _fail("bankId contains unsupported characters")
    expected_manifest = root / BANK_ROOT / bank_id / "manifest.json"
    if manifest_resolved != expected_manifest.resolve(strict=True):
        _fail("Manifest path must match assets/characters/banks/<bankId>/manifest.json")
    bank_dir = expected_manifest.parent.resolve(strict=True)
    if not bank_dir.is_relative_to(root):
        _fail("Character bank directory escapes project root")
    _reject_symlink_components(root, bank_dir)

    version = manifest.get("version")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        _fail("version must be a positive integer")
    _non_empty_string(manifest.get("title"), "title")
    if manifest.get("rigId") != RIG_ID or manifest.get("rigSchemaVersion") != RIG_SCHEMA_VERSION:
        _fail(f"Bank must target {RIG_ID} schema {RIG_SCHEMA_VERSION}")
    if manifest.get("offline") is not True:
        _fail("Character bank must be marked offline")

    policy = manifest.get("licensePolicy")
    if not isinstance(policy, dict):
        _fail("licensePolicy must be an object")
    if policy.get("allowed") != [ALLOWED_LICENSE]:
        _fail(f"licensePolicy.allowed must be exactly [{ALLOWED_LICENSE}]")
    if policy.get("redistribution") is not True or policy.get("offline") is not True:
        _fail("licensePolicy must allow redistribution and offline use")

    license_data = manifest.get("license")
    if not isinstance(license_data, dict) or license_data.get("id") != ALLOWED_LICENSE:
        _fail(f"Character bank license must be {ALLOWED_LICENSE}")
    if license_data.get("evidence") != CC0_EVIDENCE:
        _fail("CC0 license evidence must point to the official CC0 1.0 deed")
    license_file = _resolve_bank_file(root, license_data.get("file"), bank_dir, "license file")
    license_text = license_file.read_text(encoding="utf-8", errors="replace").casefold()
    if "cc0 1.0" not in license_text and "cc0-1.0" not in license_text:
        _fail("Local license file does not contain the CC0 1.0 notice")

    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        _fail("provenance must be an object")
    source_url = _non_empty_string(provenance.get("sourceUrl"), "provenance.sourceUrl")
    if not _is_https_url(source_url):
        _fail("provenance.sourceUrl must use HTTPS")
    _non_empty_string(provenance.get("publisher"), "provenance.publisher")
    authors = provenance.get("authors")
    if not isinstance(authors, list) or not authors or any(
        not isinstance(author, str) or not author.strip() for author in authors
    ):
        _fail("provenance.authors must contain at least one non-empty author")
    _non_empty_string(provenance.get("attribution"), "provenance.attribution")

    parts = manifest.get("parts")
    if not isinstance(parts, list) or not len(SLOTS) <= len(parts) <= MAX_PARTS:
        _fail(f"parts must contain between {len(SLOTS)} and {MAX_PARTS} entries")
    defaults = manifest.get("defaultParts")
    if not isinstance(defaults, dict) or set(defaults) != set(SLOTS):
        _fail("defaultParts must define exactly the six humanoid rig slots")

    part_by_id: dict[str, dict] = {}
    slot_counts = {slot: 0 for slot in SLOTS}
    seen_paths: set[str] = set()
    total_bytes = 0
    for part in parts:
        if not isinstance(part, dict):
            _fail("Every character part must be an object")
        part_id = _non_empty_string(part.get("id"), "part.id")
        if not _ID_PATTERN.fullmatch(part_id):
            _fail(f"Unsupported part id: {part_id}")
        if part_id in part_by_id:
            _fail(f"Duplicate part id: {part_id}")
        slot = _non_empty_string(part.get("slot"), f"{part_id}.slot")
        if slot not in SLOTS:
            _fail(f"Unsupported slot for {part_id}: {slot}")
        bone_id = _non_empty_string(part.get("boneId"), f"{part_id}.boneId")
        if bone_id != slot:
            _fail(f"boneId for {part_id} must match its rig slot {slot}")

        part_path = _resolve_bank_file(root, part.get("path"), bank_dir, f"{part_id}.path")
        path_key = part_path.relative_to(root).as_posix()
        if path_key in seen_paths:
            _fail(f"Duplicate texture path: {path_key}")
        seen_paths.add(path_key)
        file_size = part_path.stat().st_size
        if file_size <= 0 or file_size > MAX_PART_BYTES:
            _fail(f"Part file size is outside the mobile budget: {part_id}")
        total_bytes += file_size
        if total_bytes > MAX_BANK_BYTES:
            _fail(f"Character bank exceeds {MAX_BANK_BYTES} bytes")
        width, height = _png_dimensions(part_path)

        declared_hash = _non_empty_string(part.get("sha256"), f"{part_id}.sha256")
        if not _SHA_PATTERN.fullmatch(declared_hash):
            _fail(f"Invalid SHA-256 format for {part_id}")
        actual_hash = hashlib.sha256(part_path.read_bytes()).hexdigest()
        if declared_hash != actual_hash:
            _fail(f"SHA-256 mismatch for character part {part_id}")

        pivot = part.get("pivot")
        if not isinstance(pivot, dict):
            _fail(f"pivot for {part_id} must be an object")
        for axis in ("x", "y"):
            value = pivot.get(axis)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                _fail(f"pivot.{axis} for {part_id} must be finite")
            if not 0.0 <= float(value) <= 1.0:
                _fail(f"pivot.{axis} for {part_id} must be between 0 and 1")
        z_index = part.get("zIndex")
        if isinstance(z_index, bool) or not isinstance(z_index, int) or not -128 <= z_index <= 128:
            _fail(f"zIndex for {part_id} must be an integer between -128 and 128")

        part_by_id[part_id] = {"slot": slot, "width": width, "height": height}
        slot_counts[slot] += 1

    missing_slots = [slot for slot, count in slot_counts.items() if count == 0]
    if missing_slots:
        _fail("Character bank is missing rig slots: " + ", ".join(missing_slots))
    for slot in SLOTS:
        default_id = defaults.get(slot)
        if not isinstance(default_id, str) or default_id not in part_by_id:
            _fail(f"defaultParts.{slot} must reference an existing part")
        if part_by_id[default_id]["slot"] != slot:
            _fail(f"defaultParts.{slot} references a part that does not belong to slot {slot}")

    return {
        "bankId": bank_id,
        "partCount": len(parts),
        "slotCount": len(SLOTS),
        "slotVariants": slot_counts,
        "totalBytes": total_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path relative to the project root")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Godot project root (defaults to the repository root)",
    )
    args = parser.parse_args()
    try:
        result = validate_bank(args.root, args.manifest)
    except BankValidationError as error:
        parser.exit(1, f"CHARACTER_BANK_INVALID: {error}\n")
    print(
        "CHARACTER_BANK_OK "
        f"bank={result['bankId']} parts={result['partCount']} "
        f"slots={result['slotCount']} bytes={result['totalBytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
