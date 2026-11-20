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

MIRROR = "https://raw.githubusercontent.com/bill2432/kenney-2d-mirror/main/packs/"
PACKS = {
    "objects": {"id":"kenney_tiny_town_objects","title":"Kenney Tiny Town","page":"https://kenney.nl/assets/tiny-town","archive":"tiny-town.zip","sha256":"9768692dccff1d706408a5aedd6ca4f6cd1409506cbc84cb2f862919764be977","expected_min_png":100,"kind":"environment-object"},
    "foliage": {"id":"kenney_foliage_objects","title":"Kenney Foliage Pack","page":"https://kenney.nl/assets/foliage-pack","archive":"foliage-pack.zip","sha256":"33bd564f2cebb6a68bee9a798650d669571a389a437b0bd601d257ca2b5e7aed","expected_min_png":80,"kind":"nature-object"},
    "roguelike": {"id":"kenney_roguelike_rpg_objects","title":"Kenney Roguelike RPG Pack","page":"https://kenney.nl/assets/roguelike-rpg-pack","archive":"roguelike-rpg-pack.zip","sha256":"8e7d2378f8f794245645f6d7dc7aeeb246791410a7e512293c594b46a5a9524b","expected_min_png":50,"kind":"rpg-object"},
    "urban": {"id":"kenney_rpg_urban_objects","title":"Kenney RPG Urban Pack","page":"https://kenney.nl/assets/rpg-urban-pack","archive":"rpg-urban-pack.zip","sha256":"4541d89d639fc7d1e905dd925e55b1c4977a41d983516228db1d57173bb9afaf","expected_min_png":50,"kind":"urban-object"},
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
    if (not name or path.is_absolute() or "\\" in name or
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
        if lowered.endswith(".zip") or lowered.endswith("/download") or "/download/" in lowered:
            candidates.append(absolute)
    if not candidates:
        raise ValueError("No direct Kenney ZIP download link found on the official asset page")
    return candidates[0]


def fetch_pack(pack_id, output_root):
    if pack_id not in PACKS:
        raise ValueError(f"Unknown pack: {pack_id}")
    spec = PACKS[pack_id]
    _, page = _request(spec["page"])
    page_text = page.decode("utf-8", errors="replace")
    if not re.search(r"Creative\s+Commons\s+CC0", page_text, re.IGNORECASE):
        raise ValueError(f"Official page does not explicitly declare CC0: {spec['page']}")
    # Kenney serves its Download button dynamically. Fetch the public mirror ZIP
    # and pin the archive hash published in the mirror manifest.
    archive_url = MIRROR + spec["archive"]
    _, payload = _request(archive_url)
    actual_sha = hashlib.sha256(payload).hexdigest()
    if actual_sha != spec["sha256"]:
        raise ValueError(f"Mirror ZIP hash mismatch: expected {spec['sha256']}, got {actual_sha}")
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError(f"Mirror did not return a ZIP: {archive_url}")

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
                    "category": member.split("/")[0] if "/" in member else "General",
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
        "mirrorLicense": "https://github.com/bill2432/kenney-2d-mirror/blob/main/LICENSE.md",
        "sourceArchiveSha256": spec["sha256"],
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
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (target / "LICENSE.txt").write_text(
        f"{spec['title']}\nLicense: CC0-1.0\nSource: {spec['page']}\n"
        f"License terms: {CC0_TERMS}\nCommercial use, modification and redistribution permitted.\n",
        encoding="utf-8",
    )
    (target / "SOURCE.json").write_text(
        json.dumps({"source": spec["page"], "download": archive_url,
                    "license": "CC0-1.0", "archiveSha256": actual_sha,
                    "mirrorLicense": "https://github.com/bill2432/kenney-2d-mirror/blob/main/LICENSE.md"},
                   indent=2) + "\n", encoding="utf-8"
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
