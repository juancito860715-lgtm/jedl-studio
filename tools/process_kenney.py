#!/usr/bin/env python3
"""Download, safely inventory, and (when reviewed mapping exists) import Kenney's CC0 pack.

The archive's sprite filenames are treated as data, never guessed into rig slots.
A reviewed mapping is required before a Kenney manifest is emitted.
"""
import argparse
import hashlib
import io
import json
import os
import stat
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "avatar_bank"))
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from PIL import Image

SOURCES = (
    "https://kenney.nl/media/pages/assets/modular-character-pack/d86666b153-1677699701/kenney_modular-characters.zip",
    "https://opengameart.org/sites/default/files/Kenney_characterPack_1.zip",
)
SOURCE_PAGE = "https://opengameart.org/content/modular-character-pack"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"


def download_archive(destination: Path) -> str:
    errors = []
    request_headers = {"User-Agent": "JEDL-Studio-asset-import/1.0"}
    for url in SOURCES:
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
                if not zipfile.is_zipfile(io.BytesIO(payload)):
                    raise ValueError(f"Response from {url} is not a ZIP archive")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
                print(f"Downloaded {len(payload)} bytes from {url}")
                return url
        except Exception as exc:
            message = f"{url}: {type(exc).__name__}: {exc}"
            errors.append(message)
            print(f"DOWNLOAD ATTEMPT FAILED: {message}", file=sys.stderr)
    raise RuntimeError("All official/source archive URLs failed:\n" + "\n".join(errors))


def safe_member(name: str) -> str:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or "\\" in name or any(p in ("", ".", "..") for p in path.parts):
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    return path.as_posix()


def inventory_archive(zip_path: Path, output_dir: Path) -> dict:
    rows = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = safe_member(info.filename.rstrip("/")) if info.filename.rstrip("/") else ""
            if not name or info.is_dir():
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"ZIP contains a symbolic link: {name}")
            if not name.lower().endswith(".png"):
                continue
            raw = archive.read(info)
            with Image.open(io.BytesIO(raw)) as image:
                rgba = image.convert("RGBA")
                alpha_bbox = rgba.getchannel("A").getbbox()
                rows.append({
                    "sourceFile": name,
                    "width": rgba.width,
                    "height": rgba.height,
                    "hasTransparency": rgba.getchannel("A").getextrema()[0] < 255,
                    "hasVisiblePixels": alpha_bbox is not None,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                })
    if not rows:
        raise ValueError("The downloaded archive contains no PNG sprites")
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = {
        "source": SOURCE_PAGE,
        "license": "CC0-1.0",
        "licenseEvidence": SOURCE_PAGE,
        "licenseTerms": LICENSE_URL,
        "archiveSha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "pngCount": len(rows),
        "pngFiles": rows,
    }
    (output_dir / "kenney_inventory.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"KENNEY INVENTORY: {len(rows)} PNG files")
    for row in rows:
        print(f"PNG {row['width']}x{row['height']} {row['sourceFile']}")
    return inventory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default="build/kenney/kenney.zip")
    parser.add_argument("--out", default="app/src/main/assets/styles/kenney")
    parser.add_argument("--mapping", default="tools/avatar_bank/external_packs/kenney_modular_character_pack.mapping.json")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    zip_path = Path(args.zip)
    if args.download or not zip_path.is_file():
        source_url = download_archive(zip_path)
    else:
        source_url = "provided-local-archive"
    print(f"Archive source: {source_url}")
    inventory = inventory_archive(zip_path, Path("build/kenney"))
    mapping_path = Path(args.mapping)
    if not mapping_path.is_file():
        print(
            "KENNEY_IMPORT_PENDING: archive downloaded and inventoried, but no reviewed "
            "sprite-to-slot/bone mapping exists yet. Refusing to invent pivots, z-order, "
            "or default body-part assignments. Inventory is available at "
            "build/kenney/kenney_inventory.json.",
            file=sys.stderr,
        )
        return 0

    from import_kenney_pack import import_kenney_pack
    import_kenney_pack(zip_path, mapping_path, Path(args.out))
    manifest = json.loads((Path(args.out) / "manifest.json").read_text(encoding="utf-8"))
    print(f"KENNEY_IMPORT_OK: {len(manifest['parts'])} mapped parts; {inventory['pngCount']} PNGs inventoried.")


if __name__ == "__main__":
    main()
