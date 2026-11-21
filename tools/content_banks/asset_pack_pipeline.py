#!/usr/bin/env python3
"""Download and package reviewed CC0 art sources for JEDL's offline library.

The resulting archives are CI artifacts, not APK payloads. This keeps the
application small while making the content available for later offline import.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import stat
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

CC0_TERMS = "https://creativecommons.org/publicdomain/zero/1.0/"
KENNEY_SUPPORT = "https://kenney.nl/support"
USER_AGENT = "JEDL-Studio-Asset-Library/1.0"
MAX_ARCHIVE_BYTES = 500 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_ARCHIVE_FILES = 50000

# Every entry is checked against its live official Kenney page before download.
# The catalog intentionally lists neutral creative resources only.
KENNEY_PACKS = {
    "animal-pack": {
        "id": "kenney-animal-pack", "title": "Animal Pack",
        "category": "animals", "dimension": "2d", "expected_files": 80,
        "page": "https://kenney.nl/assets/animal-pack",
        "download": "https://kenney.nl/media/pages/assets/animal-pack/480cf9f223-1677669996/kenney_animal-pack.zip",
    },
    "animal-pack-remastered": {
        "id": "kenney-animal-pack-remastered", "title": "Animal Pack Remastered",
        "category": "animals", "dimension": "2d", "expected_files": 240,
        "page": "https://kenney.nl/assets/animal-pack-remastered",
        "download": "https://kenney.nl/media/pages/assets/animal-pack-remastered/54a307a369-1774771709/kenney_animal-pack-remastered.zip",
    },
    "furniture-kit": {
        "id": "kenney-furniture-kit", "title": "Furniture Kit",
        "category": "furniture", "dimension": "3d", "expected_files": 140,
        "page": "https://kenney.nl/assets/furniture-kit",
        "download": "https://kenney.nl/media/pages/assets/furniture-kit/440e0608a4-1677580847/kenney_furniture-kit.zip",
    },
    "mini-characters": {
        "id": "kenney-mini-characters", "title": "Mini Characters",
        "category": "characters", "dimension": "3d", "expected_files": 25,
        "page": "https://kenney.nl/assets/mini-characters",
        "download": "https://kenney.nl/media/pages/assets/mini-characters/bfc7e272b4-1774770718/kenney_mini-characters.zip",
    },
    "city-kit-suburban": {
        "id": "kenney-city-kit-suburban", "title": "City Kit Suburban",
        "category": "environment", "dimension": "3d", "expected_files": 40,
        "page": "https://kenney.nl/assets/city-kit-suburban",
        "download": "https://kenney.nl/media/pages/assets/city-kit-suburban/2c871b7af2-1745479373/kenney_city-kit-suburban_20.zip",
    },
    "nature-kit": {
        "id": "kenney-nature-kit", "title": "Nature Kit",
        "category": "environment", "dimension": "3d", "expected_files": 330,
        "page": "https://kenney.nl/assets/nature-kit",
        "download": "https://kenney.nl/media/pages/assets/nature-kit/37ac38a37b-1677698939/kenney_nature-kit.zip",
    },
    "food-kit": {
        "id": "kenney-food-kit", "title": "Food Kit",
        "category": "food", "dimension": "3d", "expected_files": 200,
        "page": "https://kenney.nl/assets/food-kit",
        "download": "https://kenney.nl/media/pages/assets/food-kit/83086fa91c-1719418518/kenney_food-kit.zip",
    },
    "toy-car-kit": {
        "id": "kenney-toy-car-kit", "title": "Toy Car Kit",
        "category": "vehicles", "dimension": "3d", "expected_files": 100,
        "page": "https://kenney.nl/assets/toy-car-kit",
        "download": "https://kenney.nl/media/pages/assets/toy-car-kit/42e19cc426-1736346027/kenney_toy-car-kit.zip",
    },
    "building-kit": {
        "id": "kenney-building-kit", "title": "Building Kit",
        "category": "environment", "dimension": "3d", "expected_files": 80,
        "page": "https://kenney.nl/assets/building-kit",
        "download": "https://kenney.nl/media/pages/assets/building-kit/0de7aaa492-1743244741/kenney_building-kit.zip",
    },
    "music-jingles": {
        "id": "kenney-music-jingles", "title": "Music Jingles",
        "category": "audio", "dimension": "audio", "expected_files": 85,
        "page": "https://kenney.nl/assets/music-jingles",
        "download": "https://kenney.nl/media/pages/assets/music-jingles/f37e530b9e-1677590399/kenney_music-jingles.zip",
    },
    "interface-sounds": {
        "id": "kenney-interface-sounds", "title": "Interface Sounds",
        "category": "audio", "dimension": "audio", "expected_files": 100,
        "page": "https://kenney.nl/assets/interface-sounds",
        "download": "https://kenney.nl/media/pages/assets/interface-sounds/fa43c1dd4d-1677589452/kenney_interface-sounds.zip",
    },
}

SAFE_COMMUNITY_CATEGORIES = ("modern-urban", "nature")


class AssetPackError(ValueError):
    pass


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(html.unescape(href))


def validate_cc0_source(text: str) -> bool:
    if not isinstance(text, str) or not re.search(
        r"\bCC0(?:[- ]1\.0)?\b|Creative Commons Zero", text, re.IGNORECASE
    ):
        raise AssetPackError("Explicit CC0 evidence is missing")
    return True


def safe_archive_member(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or "\\" in name
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise AssetPackError(f"Unsafe archive path: {name!r}")
    return path.as_posix()


def _request(url: str) -> tuple[str, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            final_url = response.geturl()
            parsed = urllib.parse.urlparse(final_url)
            if parsed.scheme != "https" or not (
                parsed.hostname == "kenney.nl" or (parsed.hostname or "").endswith(".kenney.nl")
            ):
                raise AssetPackError("Download redirect left the official Kenney HTTPS domain")
            return final_url, response.read(MAX_ARCHIVE_BYTES + 1)
    except AssetPackError:
        raise
    except Exception as exc:
        raise AssetPackError(f"Request failed for {url}: {exc}") from exc


def _resolve_kenney_download(page_url: str, page_html: bytes) -> str:
    parser = _AnchorParser()
    parser.feed(page_html.decode("utf-8", errors="replace"))
    candidates = []
    for href in parser.links:
        absolute = urllib.parse.urljoin(page_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme == "https" and parsed.hostname in ("kenney.nl", "www.kenney.nl"):
            if parsed.path.lower().endswith("/download") or parsed.path.lower().endswith(".zip"):
                candidates.append(absolute)
    if not candidates:
        raise AssetPackError(f"No official download link found on {page_url}")
    return candidates[0]


def _inspect_zip(payload: bytes) -> dict:
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise AssetPackError("Archive exceeds the configured compressed-size ceiling")
    from io import BytesIO
    import zipfile

    if not zipfile.is_zipfile(BytesIO(payload)):
        raise AssetPackError("Official download did not return a ZIP archive")
    files = []
    formats = {}
    total_uncompressed = 0
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_FILES:
            raise AssetPackError("Archive contains too many entries")
        for info in infos:
            if info.is_dir():
                continue
            member = safe_archive_member(info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise AssetPackError(f"Symbolic link rejected: {member}")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise AssetPackError("Archive exceeds the configured expanded-size ceiling")
            extension = Path(member).suffix.lower() or "[no-extension]"
            formats[extension] = formats.get(extension, 0) + 1
            files.append({"path": member, "bytes": info.file_size, "extension": extension})
        if not files:
            raise AssetPackError("Archive contains no files")
        if archive.testzip() is not None:
            raise AssetPackError("ZIP CRC validation failed")
    return {
        "fileCount": len(files),
        "uncompressedBytes": total_uncompressed,
        "formats": dict(sorted(formats.items())),
        "files": files,
    }


def download_kenney_pack(pack_key: str, output_root: Path) -> dict:
    if pack_key not in KENNEY_PACKS:
        raise AssetPackError(f"Unknown Kenney pack key: {pack_key}")
    spec = KENNEY_PACKS[pack_key]
    _, page = _request(spec["page"])
    page_text = page.decode("utf-8", errors="replace")
    validate_cc0_source(page_text)
    download_url = spec["download"]
    if not download_url.startswith("https://kenney.nl/media/pages/assets/"):
        raise AssetPackError(f"Unapproved Kenney download URL for {pack_key}")
    final_url, payload = _request(download_url)
    archive_info = _inspect_zip(payload)

    target = Path(output_root) / spec["id"]
    target.mkdir(parents=True, exist_ok=True)
    archive_name = spec["id"] + ".zip"
    archive_path = target / archive_name
    archive_path.write_bytes(payload)
    archive_sha = hashlib.sha256(payload).hexdigest()
    manifest = {
        "schemaVersion": 1,
        "id": spec["id"],
        "title": spec["title"],
        "publisher": "Kenney",
        "source": spec["page"],
        "downloadUrl": final_url,
        "license": "CC0-1.0",
        "licenseTerms": CC0_TERMS,
        "licenseEvidence": spec["page"],
        "licensePolicyEvidence": KENNEY_SUPPORT,
        "commercialUse": True,
        "modificationAllowed": True,
        "redistributionAllowed": True,
        "offlineAppPackAllowed": True,
        "attributionRequired": False,
        "attributionNote": "Optional courtesy credit: Kenney",
        "category": spec["category"],
        "dimension": spec["dimension"],
        "expectedFileCountFromPublisher": spec["expected_files"],
        "archive": archive_name,
        "archiveBytes": len(payload),
        "archiveSha256": archive_sha,
        **archive_info,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (target / "LICENSE.txt").write_text(
        f"{spec['title']}\nPublisher: Kenney\nLicense: CC0-1.0\n"
        f"Source: {spec['page']}\nLicense terms: {CC0_TERMS}\n"
        "Commercial use, modification and redistribution are permitted under CC0.\n",
        encoding="utf-8",
    )
    print(
        f"ASSET_PACK_OK id={spec['id']} files={archive_info['fileCount']} "
        f"category={spec['category']} sha256={archive_sha}"
    )
    return manifest


def download_kenney_catalog(output_root: Path) -> list[dict]:
    manifests = []
    for key in KENNEY_PACKS:
        manifests.append(download_kenney_pack(key, output_root))
    index = {
        "schemaVersion": 1,
        "source": "Kenney",
        "license": "CC0-1.0",
        "packCount": len(manifests),
        "packs": [
            {
                "id": item["id"],
                "category": item["category"],
                "dimension": item["dimension"],
                "archive": f"{item['id']}/{item['archive']}",
                "sha256": item["archiveSha256"],
                "fileCount": item["fileCount"],
            }
            for item in manifests
        ],
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (Path(output_root) / "catalog.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifests


def package_community_assets(source_root: Path, output_zip: Path) -> dict:
    import zipfile

    source_root = Path(source_root)
    output_zip = Path(output_zip)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    file_records = []
    pack_count = 0
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for category in SAFE_COMMUNITY_CATEGORIES:
            category_root = source_root / category
            if not category_root.is_dir():
                raise AssetPackError(f"Required source category is missing: {category}")
            for pack_root in sorted(path for path in category_root.iterdir() if path.is_dir()):
                source_file = pack_root / "SOURCE.md"
                if not source_file.is_file():
                    raise AssetPackError(f"Missing per-pack source/license evidence: {source_file}")
                source_text = source_file.read_text(encoding="utf-8", errors="replace")
                validate_cc0_source(source_text)
                pack_count += 1
                for file_path in sorted(pack_root.rglob("*")):
                    if file_path.is_symlink():
                        raise AssetPackError(f"Symbolic links are not accepted: {file_path}")
                    if not file_path.is_file():
                        continue
                    relative = file_path.relative_to(source_root).as_posix()
                    safe_archive_member(relative)
                    raw = file_path.read_bytes()
                    digest = hashlib.sha256(raw).hexdigest()
                    archive.write(file_path, relative)
                    file_records.append({
                        "path": relative,
                        "bytes": len(raw),
                        "sha256": digest,
                        "pack": pack_root.name,
                        "category": category,
                    })
        if not file_records or not pack_count:
            raise AssetPackError("No CC0 community packs were found")
        index = {
            "schemaVersion": 1,
            "publisher": "Tiddybub/2d-assets",
            "sourceRepository": "https://github.com/Tiddybub/2d-assets",
            "sourceCategories": list(SAFE_COMMUNITY_CATEGORIES),
            "license": "CC0-1.0",
            "licenseEvidence": "Each included pack retains its original SOURCE.md",
            "packCount": pack_count,
            "fileCount": len(file_records),
            "files": file_records,
        }
        archive.writestr(
            "JEDL-PACKAGE.json",
            json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        )
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    kenney = sub.add_parser("download-kenney")
    kenney.add_argument("--out", default="build/asset-library/kenney")
    community = sub.add_parser("package-community")
    community.add_argument("--source", required=True)
    community.add_argument("--out", default="build/asset-library/community-2d.zip")
    args = parser.parse_args()

    try:
        if args.command == "download-kenney":
            manifests = download_kenney_catalog(Path(args.out))
            print(f"KENNEY_CATALOG_OK packs={len(manifests)}")
        else:
            result = package_community_assets(Path(args.source), Path(args.out))
            print(f"COMMUNITY_2D_OK packs={result['packCount']} files={result['fileCount']}")
        return 0
    except (AssetPackError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"ASSET_PACK_ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
