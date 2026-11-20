#!/usr/bin/env python3
"""Forensic inventory of the downloaded RGS character archive.

Groups every PNG by its path relative to the extraction root. Does not infer
anatomy, crop sprites, or assign bones.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def build_inventory(root: Path) -> dict:
    if not root.is_dir():
        raise FileNotFoundError(f"RGS extraction directory does not exist: {root}")
    grouped = defaultdict(list)
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix().casefold()):
        if path.is_file() and path.suffix.casefold() == ".png":
            relative = path.relative_to(root).as_posix()
            folder = Path(relative).parent.as_posix()
            if folder == ".":
                folder = "(root)"
            grouped[folder].append(relative)
    files = sum(len(items) for items in grouped.values())
    return {
        "source": "RGS_Dev Free CC0 Modular Animated Vector Characters 2D",
        "root": root.as_posix(),
        "pngCount": files,
        "folderCount": len(grouped),
        "folders": {name: grouped[name] for name in sorted(grouped, key=str.casefold)},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="temp_rgs")
    parser.add_argument("--output", default="rgs_inventory.json")
    args = parser.parse_args()
    root = Path(args.root)
    inventory = build_inventory(root)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("========== RGS PNG FORENSIC INVENTORY ==========")
    print(json.dumps(inventory, indent=2, ensure_ascii=False))
    print(f"RGS_INVENTORY_FILE={output}")
    print(f"RGS_PNG_COUNT={inventory['pngCount']}")
    if inventory["pngCount"] == 0:
        raise SystemExit("No PNG files found in RGS archive; inspect archive contents.")


if __name__ == "__main__":
    main()
