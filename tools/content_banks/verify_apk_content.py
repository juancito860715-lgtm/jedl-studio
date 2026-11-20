#!/usr/bin/env python3
"""Verify that all licensed content banks and their exact PNG bytes are inside the APK."""
import hashlib
import json
import zipfile
from pathlib import Path

APK = Path("app/build/outputs/apk/debug/app-debug.apk")
BANKS = [
    "characters/kenney_modular_character_pack",
    "kenney_tiny_town_objects",
    "kenney_foliage_objects",
]

def verify():
    if not APK.is_file():
        raise FileNotFoundError(APK)
    total = 0
    with zipfile.ZipFile(APK) as apk:
        names = set(apk.namelist())
        preset_path = "assets/content/character_presets.json"
        if preset_path not in names:
            raise AssertionError("Character preset catalog missing from APK")
        presets = json.loads(apk.read(preset_path))
        if presets.get("presetCount") != 8 or len(presets.get("presets", [])) != 8:
            raise AssertionError("Expected eight complete character presets")

        for bank in BANKS:
            root = "assets/content/" + bank
            manifest_path = root + "/manifest.json"
            license_path = root + "/LICENSE.txt"
            source_path = root + "/SOURCE.json"
            for required in (manifest_path, license_path, source_path):
                if required not in names:
                    raise AssertionError("Missing packaged bank metadata: " + required)
            manifest = json.loads(apk.read(manifest_path))
            if manifest.get("license") != "CC0-1.0":
                raise AssertionError("Unexpected license in " + bank)
            if not manifest.get("commercialUse") or not manifest.get("apkRedistributionAllowed"):
                raise AssertionError("Redistribution rights missing in " + bank)
            entries = manifest.get("assets", [])
            if not entries:
                raise AssertionError("Empty bank: " + bank)
            for item in entries:
                path = root + "/" + item["file"]
                if path not in names:
                    raise AssertionError("Missing APK asset: " + path)
                raw = apk.read(path)
                if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                    raise AssertionError("SHA-256 mismatch: " + path)
                if not path.lower().endswith(".png"):
                    raise AssertionError("Non-PNG item in PNG bank: " + path)
            total += len(entries)
            print("APK_BANK_OK", manifest["id"], "png=", len(entries), "license=CC0-1.0")
    print("APK_CONTENT_OK banks=", len(BANKS), "png=", total, "presets=8")

if __name__ == "__main__":
    verify()
