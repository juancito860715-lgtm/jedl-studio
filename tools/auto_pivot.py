#!/usr/bin/env python3
"""Measure attachment pivots from visible alpha pixels in original RGS sprites."""
import argparse
import json
from pathlib import Path
from PIL import Image


RGS_ROOT_NAME = "Free 2D Animated Vector Game Character Sprites/Animated body parts"
SOURCES = {
    "head": ("Heads/head1/idle_0.png", "bottom"),
    "hand_l": ("Left hands/handL1/idle_0.png", "top"),
    "hand_r": ("Right hands/handR1/idle_0.png", "top"),
    "foot_l": ("Left feet/footL1/idle_0.png", "top"),
    "foot_r": ("Right feet/footR1/idle_0.png", "top"),
}


def measure(path: Path, edge: str) -> dict:
    with Image.open(path) as source:
        alpha = source.convert("RGBA").getchannel("A")
        width, height = alpha.size
        pixels = alpha.load()
        rows = []
        for y in range(height):
            weighted_x = 0
            total_alpha = 0
            for x in range(width):
                value = pixels[x, y]
                if value:
                    weighted_x += (x + 0.5) * value
                    total_alpha += value
            if total_alpha:
                rows.append((y, weighted_x, total_alpha))
        if not rows:
            raise ValueError(f"No visible alpha pixels in {path}")
        y, weighted_x, total_alpha = rows[-1] if edge == "bottom" else rows[0]
        x = weighted_x / total_alpha
        return {
            "pivotX": x / width,
            "pivotY": (y + 0.5) / height,
            "pixelX": x,
            "pixelY": y + 0.5,
            "imageWidth": width,
            "imageHeight": height,
            "edge": edge,
            "alphaPixelsOnEdgeRow": total_alpha,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rgs-root", default="temp_rgs")
    parser.add_argument("--output", default="rgs_auto_pivots.json")
    args = parser.parse_args()
    root = Path(args.rgs_root) / RGS_ROOT_NAME
    result = {}
    for key, (relative, edge) in SOURCES.items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required RGS sprite missing for pivot measurement: {path}")
        result[key] = {"source": relative, **measure(path, edge)}
    # Facial overlays share the original head canvas and the exact measured head pivot.
    result["eyes"] = dict(result["head"], source=SOURCES["head"][0])
    result["mouth"] = dict(result["head"], source=SOURCES["head"][0])
    result["hair"] = dict(result["head"], source=SOURCES["head"][0])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    head = result["head"]
    print(f"Pivote de Cabeza medido: X={head['pivotX']:.8f} Y={head['pivotY']:.8f}")
    for key in ("hand_l", "hand_r", "foot_l", "foot_r"):
        pivot = result[key]
        print(f"Pivote {key} medido: X={pivot['pivotX']:.8f} Y={pivot['pivotY']:.8f}")
    print(f"AUTO_PIVOTS_JSON={output}")


if __name__ == "__main__":
    main()
