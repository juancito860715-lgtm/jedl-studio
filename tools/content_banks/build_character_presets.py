#!/usr/bin/env python3
"""Build rig-compatible character presets from the real generated avatar manifest."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/avatar_bank/out/manifest.json"
OUTPUT = ROOT / "app/src/main/assets/content/character_presets.json"

PRESETS = [
    ("master_default", "Personaje maestro", "Apariencia base del rig JEDL", {}),
    ("hair_spiky", "Cabello puntiagudo", "Variante de cabello puntiagudo", {
        "HAIR_BACK": "hair_spiky_back", "HAIR_FRONT": "hair_spiky_front"
    }),
    ("hair_curly", "Cabello rizado", "Variante de cabello rizado", {
        "HAIR_BACK": "hair_curly_back", "HAIR_FRONT": "hair_curly_front"
    }),
    ("expression_happy", "Expresión alegre", "Ojos alegres y sonrisa", {
        "EYES": "face_eyes_happy", "MOUTH": "face_mouth_smile"
    }),
    ("expression_surprised", "Expresión sorprendida", "Ojos abiertos y boca expresiva", {
        "EYES": "face_eyes_wide", "MOUTH": "face_mouth_open"
    }),
    ("urban_cap", "Gorra urbana", "Gorra de tres piezas sobre el personaje", {
        "HAT_BACK": "hat_cap_crown", "HAT_FRONT": "hat_cap_panel"
    }),
    ("cap_brim", "Gorra con visera", "Gorra completa con visera", {
        "HAT_BACK": "hat_cap_crown", "HAT_FRONT": "hat_cap_brim"
    }),
    ("closed_hands", "Manos cerradas", "Puños para poses de acción", {
        "HAND_L": "hand_fist_L", "HAND_R": "hand_fist_R"
    }),
]

def build():
    manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    parts = {item["id"]: item for item in manifest["parts"]}
    defaults = manifest["defaults"]
    result = []
    for preset_id, title, description, overrides in PRESETS:
        selected = dict(defaults)
        for slot, part_id in overrides.items():
            if part_id not in parts or parts[part_id]["slot"] != slot:
                raise ValueError(f"Preset {preset_id} has invalid part {slot}={part_id}")
            selected[slot] = part_id
        result.append({
            "id": preset_id,
            "title": title,
            "description": description,
            "selectedParts": selected,
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "schemaVersion": 1,
        "id": "jedl_character_presets",
        "sourceManifest": "jedl_master_v1",
        "rigId": manifest["rigId"],
        "presetCount": len(result),
        "presets": result,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CHARACTER_PRESETS_OK count={len(result)} path={OUTPUT}")
    return result

if __name__ == "__main__":
    build()
