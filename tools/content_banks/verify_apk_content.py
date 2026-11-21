#!/usr/bin/env python3
"""Verify that all licensed content banks and their exact PNG bytes are inside the APK."""
import hashlib
import json
import zipfile
from io import BytesIO
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

        model_path = "assets/models/pose_landmarker_lite.task"
        if model_path not in names:
            raise AssertionError("MediaPipe Lite model missing from APK")
        model_sha = hashlib.sha256(apk.read(model_path)).hexdigest()
        expected_model_sha = "59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a"
        if model_sha != expected_model_sha:
            raise AssertionError("MediaPipe Lite model SHA-256 mismatch: " + model_sha)

        bundle_path = "assets/offline_library/jedl-library-bundle.zip"
        if bundle_path not in names:
            raise AssertionError("Installable offline library ZIP missing from APK")
        bundle_bytes = apk.read(bundle_path)
        with zipfile.ZipFile(BytesIO(bundle_bytes)) as bundle:
            if bundle.testzip() is not None:
                raise AssertionError("Offline library ZIP CRC failure")
            package_manifest = json.loads(bundle.read("JEDL-PACKAGE.json"))
            if package_manifest.get("id") != "jedl-offline-library":
                raise AssertionError("Unexpected offline library package ID")
            if package_manifest.get("license") != "CC0-1.0" or not package_manifest.get("redistributionAllowed"):
                raise AssertionError("Offline package license/redistribution contract invalid")
            for item in package_manifest.get("files", []):
                raw = bundle.read(item["path"])
                if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                    raise AssertionError("Offline package SHA-256 mismatch: " + item["path"])
        print("APK_OFFLINE_PACKAGE_OK files=", len(package_manifest["files"]),
              "sha256=", hashlib.sha256(bundle_bytes).hexdigest())
        print("APK_MEDIAPIPE_LITE_OK sha256=", model_sha)

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
