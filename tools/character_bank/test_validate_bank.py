#!/usr/bin/env python3
"""TDD tests for the offline, rig-compatible character-bank contract."""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from validate_bank import BankValidationError, validate_bank

SLOTS = ("head", "torso", "arm_left", "arm_right", "leg_left", "leg_right")
BANK_ID = "jedl_humanoid_cc0_v1"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def _png(width: int = 16, height: int = 16, color_type: int = 6) -> bytes:
    channels = {2: 3, 4: 2, 6: 4}[color_type]
    row = b"\x00" + bytes([255]) * width * channels
    pixels = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(pixels))
        + _chunk(b"IEND", b"")
    )


class CharacterBankContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bank_dir = self.root / "assets" / "characters" / "banks" / BANK_ID
        (self.bank_dir / "parts").mkdir(parents=True)
        self.license_path = self.bank_dir / "LICENSE.txt"
        self.license_path.write_text(
            "Creative Commons CC0 1.0 Universal\n", encoding="utf-8"
        )
        self.manifest_path = self.bank_dir / "manifest.json"
        self.manifest = self._build_valid_manifest()
        self._write_manifest()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _build_valid_manifest(self) -> dict:
        parts = []
        defaults = {}
        for index, slot in enumerate(SLOTS):
            relative = f"parts/{slot}.png"
            file_path = self.bank_dir / relative
            file_path.write_bytes(_png())
            part_id = f"{slot}.base"
            defaults[slot] = part_id
            parts.append(
                {
                    "id": part_id,
                    "slot": slot,
                    "boneId": slot,
                    "path": f"res://assets/characters/banks/{BANK_ID}/{relative}",
                    "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
                    "pivot": {"x": 0.5, "y": 0.5},
                    "zIndex": index,
                }
            )
        return {
            "schemaVersion": 1,
            "bankId": BANK_ID,
            "version": 1,
            "title": "Synthetic test bank",
            "rigId": "jedl_humanoid_v1",
            "rigSchemaVersion": 1,
            "offline": True,
            "licensePolicy": {
                "allowed": ["CC0-1.0"],
                "redistribution": True,
                "offline": True,
            },
            "license": {
                "id": "CC0-1.0",
                "evidence": "https://creativecommons.org/publicdomain/zero/1.0/",
                "file": f"res://assets/characters/banks/{BANK_ID}/LICENSE.txt",
            },
            "provenance": {
                "sourceUrl": "https://example.org/synthetic-fixture",
                "publisher": "JEDL Studio test fixture",
                "authors": ["JEDL Studio test fixture"],
                "attribution": "Synthetic test data; no third-party artwork.",
            },
            "parts": parts,
            "defaultParts": defaults,
        }

    def _write_manifest(self) -> None:
        self.manifest_path.write_text(
            json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8"
        )

    def _part(self, slot: str) -> dict:
        return next(part for part in self.manifest["parts"] if part["slot"] == slot)

    def _refresh_hash(self, part: dict) -> None:
        relative = part["path"].removeprefix("res://")
        part["sha256"] = hashlib.sha256((self.root / relative).read_bytes()).hexdigest()

    def _assert_invalid(self, message_fragment: str) -> None:
        self._write_manifest()
        with self.assertRaises(BankValidationError) as raised:
            validate_bank(self.root, self.manifest_path)
        self.assertIn(message_fragment.lower(), str(raised.exception).lower())

    def test_valid_six_slot_bank_is_accepted(self) -> None:
        result = validate_bank(self.root, self.manifest_path)
        self.assertEqual(result["bankId"], BANK_ID)
        self.assertEqual(result["partCount"], 6)
        self.assertEqual(result["slotCount"], 6)

    def test_multiple_variants_for_one_slot_are_supported(self) -> None:
        original = self._part("head")
        alternate_path = self.bank_dir / "parts" / "head_alt.png"
        alternate_path.write_bytes(_png(20, 20))
        alternate = dict(original)
        alternate["id"] = "head.alternate"
        alternate["path"] = f"res://assets/characters/banks/{BANK_ID}/parts/head_alt.png"
        alternate["sha256"] = hashlib.sha256(alternate_path.read_bytes()).hexdigest()
        self.manifest["parts"].append(alternate)
        self._write_manifest()
        result = validate_bank(self.root, self.manifest_path)
        self.assertEqual(result["partCount"], 7)

    def test_missing_required_slot_is_rejected(self) -> None:
        self.manifest["parts"] = [
            part for part in self.manifest["parts"] if part["slot"] != "leg_left"
        ]
        head = self._part("head")
        alternate_path = self.bank_dir / "parts" / "head_alt.png"
        alternate_path.write_bytes(_png(20, 20))
        alternate = dict(head)
        alternate["id"] = "head.alternate"
        alternate["path"] = f"res://assets/characters/banks/{BANK_ID}/parts/head_alt.png"
        alternate["sha256"] = hashlib.sha256(alternate_path.read_bytes()).hexdigest()
        self.manifest["parts"].append(alternate)
        self._assert_invalid("missing rig slots")

    def test_unknown_slot_is_rejected(self) -> None:
        self._part("head")["slot"] = "face"
        self._assert_invalid("unsupported slot")

    def test_bone_mapping_must_match_rig_slot(self) -> None:
        self._part("arm_left")["boneId"] = "arm_right"
        self._assert_invalid("boneId")

    def test_duplicate_part_id_is_rejected(self) -> None:
        self.manifest["parts"][1]["id"] = self.manifest["parts"][0]["id"]
        self._assert_invalid("duplicate part id")

    def test_path_traversal_is_rejected(self) -> None:
        self._part("head")["path"] = (
            f"res://assets/characters/banks/{BANK_ID}/parts/../../../../README.md"
        )
        self._assert_invalid("unsafe")

    def test_symlink_escape_is_rejected(self) -> None:
        part = self._part("head")
        path = self.root / part["path"].removeprefix("res://")
        outside = self.root / "outside.png"
        outside.write_bytes(_png())
        path.unlink()
        try:
            path.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"Symlinks unavailable in this environment: {error}")
        self._assert_invalid("symlink")

    def test_sha256_mismatch_is_rejected(self) -> None:
        self._part("head")["sha256"] = "0" * 64
        self._assert_invalid("sha-256 mismatch")

    def test_opaque_png_is_rejected(self) -> None:
        part = self._part("head")
        path = self.root / part["path"].removeprefix("res://")
        path.write_bytes(_png(color_type=2))
        self._refresh_hash(part)
        self._assert_invalid("alpha channel")

    def test_corrupt_png_crc_is_rejected(self) -> None:
        part = self._part("head")
        path = self.root / part["path"].removeprefix("res://")
        data = bytearray(path.read_bytes())
        data[29] ^= 0x01
        path.write_bytes(data)
        self._refresh_hash(part)
        self._assert_invalid("crc")

    def test_out_of_range_pivot_is_rejected(self) -> None:
        self._part("head")["pivot"]["x"] = 1.1
        self._assert_invalid("pivot")

    def test_missing_license_notice_is_rejected(self) -> None:
        self.license_path.unlink()
        self._assert_invalid("license file")

    def test_non_https_source_is_rejected(self) -> None:
        self.manifest["provenance"]["sourceUrl"] = "http://example.org/source"
        self._assert_invalid("https")

    def test_default_part_must_match_its_slot(self) -> None:
        self.manifest["defaultParts"]["head"] = "torso.base"
        self._assert_invalid("does not belong to slot")

    def test_oversized_texture_is_rejected(self) -> None:
        part = self._part("head")
        path = self.root / part["path"].removeprefix("res://")
        path.write_bytes(_png(width=1025, height=1))
        self._refresh_hash(part)
        self._assert_invalid("dimension")

    def test_missing_part_file_is_rejected(self) -> None:
        part = self._part("head")
        (self.root / part["path"].removeprefix("res://")).unlink()
        self._assert_invalid("does not exist")


if __name__ == "__main__":
    unittest.main(verbosity=2)
