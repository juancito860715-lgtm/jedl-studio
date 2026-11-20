#!/usr/bin/env python3
"""Package the generated rig-compatible art into interchangeable style packs."""
import copy
import json
from pathlib import Path
from PIL import Image, ImageOps

PART_COUNT = 42

def build_style_packs(manifest_path: Path, png_dir: Path, output_root: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = manifest.get("parts", [])
    if len(parts) != PART_COUNT:
        raise ValueError(f"Expected {PART_COUNT} parts, got {len(parts)}")
    ids = [part["id"] for part in parts]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate part IDs in source manifest")
    defaults = manifest.get("defaults", {})
    by_id = {part["id"]: part for part in parts}
    for slot, part_id in defaults.items():
        if part_id not in by_id or by_id[part_id]["slot"] != slot:
            raise ValueError(f"Invalid default mapping: {slot} -> {part_id}")

    output_root.mkdir(parents=True, exist_ok=True)
    for style in ("default", "boceto"):
        style_root = output_root / style
        characters = style_root / "characters"
        characters.mkdir(parents=True, exist_ok=True)
        style_manifest = copy.deepcopy(manifest)
        for part in style_manifest["parts"]:
            source = png_dir / f'{part["id"]}.png'
            if not source.is_file():
                raise FileNotFoundError(f"Missing source PNG: {source}")
            with Image.open(source) as original:
                rgba = original.convert("RGBA")
                if style == "boceto":
                    gray = ImageOps.grayscale(rgba.getchannel("RGB"))
                    rgba = Image.merge("RGBA", (gray, gray, gray, rgba.getchannel("A")))
                rgba.save(characters / f'{part["id"]}.png', optimize=True)
            part["file"] = f'characters/{part["id"]}.png'
        (style_root / "manifest.json").write_text(
            json.dumps(style_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    return output_root

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    build_style_packs(here / "out" / "manifest.json", here / "out" / "png",
                      here.parent.parent / "app" / "src" / "main" / "assets" / "styles")
