#!/usr/bin/env python3
"""Fetch a Kenney CC0 pack from its official asset page and package safe PNGs.

The script verifies the live page's CC0 declaration, resolves its download link,
rejects non-Kenney hosts and unsafe ZIP paths, and writes a deterministic manifest.
"""
import argparse
import hashlib
import html
import io
import json
import re
import stat
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

PACKS = {
    "objects": {
        "id": "kenney_roguelike_rpg_objects",
        "title": "Kenney Roguelike/RPG Pack",
        "page": "https://kenney.nl/assets/roguelike-rpg-pack",
        "expected_min_png": 100,
        "kind": "object",
    },
    "characters": {
        "id": "kenney_modular_character_pack",
        "title": "Kenney Modular Character Pack",
        "page": "https://opengameart.org/content/modular-character-pack",
        "expected_min_png": 100,
        "kind": "character-part",
    },
}
CC0_TERMS = "https://creativecommons.org/publicdomain/zero/1.0/"
USER_AGENT = "JEDL-Studio-CC0-Asset-Importer/1.0"


class DownloadLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs = dict(attrs)
        href = attrs.get("href", "")
        if href:
            self.links.append(html.unescape(href))


def _request(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.geturl(), response.read()


def _safe_member(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\\\" in name or
            any(part in ("", ".", "..") for part in path.parts)):
        raise ValueError(f"Unsafe ZIP path: {name!r}")
    return path.as_posix()


def resolve_download(page_url, page_html):
    parser = DownloadLinkParser()
    parser.feed(page_html.decode("utf-8", errors="replace"))
    candidates = []
    for href in parser.links:
        absolute = urllib.parse.urljoin(page_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme != "https" or parsed.hostname not in ("kenney.nl", "www.kenney.nl"):
            continue
        lowered = parsed.path.lower()
        if lowered.endswith(".zip") or "/download/" in lowered:
            candidates.append(absolute)
    if not candidates:
        raise ValueError("No direct Kenney ZIP download link found on the official asset page")
    return candidates[0]


def fetch_pack(pack_id, output_root):
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack: {pack_id}")
    spec = PACKS[pack_id]
    final_url, page = _request(spec["page"])
    page_text = page.decode("utf-8", errors="replace")
    if not re.search(r"Creative\\s+Commons\\s+CC0", page_text, re.IGNORECASE):
        raise ValueError(f"Official page does not explicitly declare CC0: {spec['page']}")
    download_url = resolve_download(final_url, page)
    archive_url, payload = _request(download_url)
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError(f"Download endpoint did not return a ZIP: {archive_url}")

    target = Path(output_root) / spec["id"]
    png_root = target / "png"
    png_root.mkdir(parents=True, exist_ok=True)
    entries = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info in archive.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".png"):
                continue
            member = _safe_member(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"Symbolic link rejected: {member}")
            raw = archive.read(info)
            from PIL import Image
            with Image.open(io.BytesIO(raw)) as image:
                rgba = image.convert("RGBA")
                if rgba.width < 1 or rgba.height < 1:
                    raise ValueError(f"Invalid PNG dimensions: {member}")
                output = png_root / member
                output.parent.mkdir(parents=True, exist_ok=True)
                rgba.save(output, format="PNG", optimize=True)
                entries.append({
                    "id": hashlib.sha256(member.encode("utf-8")).hexdigest()[:16],
                    "file": f"png/{member}",
                    "sourceFile": member,
                    "width": rgba.width,
                    "height": rgba.height,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "kind": spec["kind"],
                    "category": "uncategorized",
                })
    if len(entries) < spec["expected_min_png"]:
        raise ValueError(f"Pack incomplete: expected at least {spec['expected_min_png']} PNGs, got {len(entries)}")
    entries.sort(key=lambda item: item["sourceFile"])
    manifest = {
        "schemaVersion": 1,
        "id": spec["id"],
        "title": spec["title"],
        "publisher": "Kenney",
        "source": spec["page"],
        "downloadSource": archive_url,
        "license": "CC0-1.0",
        "licenseTerms": CC0_TERMS,
        "commercialUse": True,
        "modificationAllowed": True,
        "apkRedistributionAllowed": True,
        "attributionRequired": False,
        "attributionNote": "Optional courtesy credit: Kenney.nl",
        "assetCount": len(entries),
        "assets": entries,
    }
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8"
    )
    (target / "LICENSE.txt").write_text(
        f"{spec['title']}\\nLicense: CC0-1.0\\nSource: {spec['page']}\\n"
        f"License terms: {CC0_TERMS}\\nCommercial use, modification and redistribution permitted.\\n",
        encoding="utf-8",
    )
    (target / "SOURCE.json").write_text(
        json.dumps({"source": spec["page"], "download": archive_url,
                    "license": "CC0-1.0", "archiveSha256": hashlib.sha256(payload).hexdigest()},
                   indent=2) + "\\n", encoding="utf-8"
    )
    print(f"PACK_OK id={spec['id']} png={len(entries)} license=CC0-1.0 output={target}")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", choices=sorted(PACKS), required=True)
    parser.add_argument("--out", default="app/src/main/assets/content")
    args = parser.parse_args()
    fetch_pack(args.pack, args.out)


if __name__ == "__main__":
    main()
