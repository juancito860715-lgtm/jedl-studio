#!/usr/bin/env python3
"""Build an offline, license-audited photorealistic Poly Haven asset bank.

Downloads are pinned to a small curated allowlist. The Android app never calls
Poly Haven at runtime: all selected assets and metadata are packaged locally.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT_2D = ROOT / "assets/gallery/2d"
OUT_3D = ROOT / "assets/gallery/3d"
CATALOG = ROOT / "assets/gallery/catalog.json"
USER_AGENT = "JEDL-Studio-Offline-Asset-Builder/1.0 (CC0 asset packaging)"

HDRIS = {
    "mossy_forest": "Bosque musgoso con arroyo",
    "xanderklinge": "Arroyo rocoso y cascada",
    "river_walk_1": "Sendero bajo dosel forestal",
    "autumn_forest_03": "Bosque otoñal con arroyo",
}
MODELS = {
    "tree_stump_01": "Tocón de árbol con musgo",
    "tree_stump_02": "Tocón de árbol envejecido",
    "dead_quiver_branch_01": "Rama seca de bosque",
    "dead_quiver_branch_02": "Tronco caído erosionado",
    "dead_quiver_trunk": "Tronco natural",
    "dead_tree_trunk_02": "Tronco caído con líquenes",
}


def request_bytes(url: str, max_bytes: int = 80_000_000) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read(max_bytes + 1)
    if not payload or len(payload) > max_bytes:
        raise ValueError(f"Download size invalid for {url}: {len(payload)} bytes")
    return payload


def get_json(url: str) -> dict:
    return json.loads(request_bytes(url, 12_000_000).decode("utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_jpeg(payload: bytes, path: Path, max_width: int = 2048) -> tuple[int, int]:
    with Image.open(io.BytesIO(payload)) as source:
        image = source.convert("RGB")
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, "JPEG", quality=91, optimize=True, progressive=True)
        return image.size


def safe_relative_path(value: str) -> Path:
    normalized = value.replace("\\\\", "/")
    path = Path(normalized)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Unsafe model include path: {value}")
    return path


def build_2d(api_assets: dict) -> list[dict]:
    entries = []
    for asset_id, title in HDRIS.items():
        metadata = api_assets.get(asset_id)
        if not metadata or metadata.get("type") != 0:
            raise ValueError(f"Missing or invalid Poly Haven HDRI: {asset_id}")
        files = get_json(f"https://api.polyhaven.com/files/{asset_id}")
        tonemapped = files.get("tonemapped", {})
        url = tonemapped.get("url")
        if not url:
            raise ValueError(f"No tonemapped photographic image for {asset_id}")
        output = OUT_2D / f"{asset_id}.jpg"
        dimensions = save_jpeg(request_bytes(url), output)
        entries.append({
            "id": f"background.{asset_id}", "title": title,
            "description": metadata.get("description", ""),
            "path": "res://" + output.relative_to(ROOT).as_posix(),
            "preview_path": "res://" + output.relative_to(ROOT).as_posix(),
            "kind": "2d", "category": "Fondos fotográficos",
            "format": "JPEG", "width": dimensions[0], "height": dimensions[1],
            "license": "CC0-1.0", "source": f"https://polyhaven.com/a/{asset_id}",
            "publisher": "Poly Haven", "authors": metadata.get("authors", {}),
            "tags": metadata.get("tags", []), "sha256": sha256(output),
            "offline": True, "placeable": True,
        })
    return entries


def choose_gltf_file(files: dict) -> dict:
    gltf = files.get("gltf", {})
    if not gltf:
        raise ValueError("Poly Haven model does not provide glTF")
    resolutions = sorted(gltf, key=lambda value: int(value[:-1]) if value.endswith("k") else 999)
    for resolution in resolutions:
        candidate = gltf[resolution].get("gltf")
        if candidate and candidate.get("url"):
            return candidate
    raise ValueError("No downloadable glTF file found")


def build_3d(api_assets: dict) -> list[dict]:
    entries = []
    for asset_id, title in MODELS.items():
        metadata = api_assets.get(asset_id)
        if not metadata or metadata.get("type") != 2:
            raise ValueError(f"Missing or invalid Poly Haven model: {asset_id}")
        polycount = int(metadata.get("polycount", 0))
        if polycount <= 0 or polycount > 200_000:
            raise ValueError(f"Model exceeds mobile polycount budget: {asset_id} ({polycount})")
        files = get_json(f"https://api.polyhaven.com/files/{asset_id}")
        gltf_file = choose_gltf_file(files)
        folder = OUT_3D / asset_id
        folder.mkdir(parents=True, exist_ok=True)
        main_name = Path(urllib.parse.urlparse(gltf_file["url"]).path).name
        if not main_name.lower().endswith((".gltf", ".glb")):
            raise ValueError(f"Unexpected glTF filename for {asset_id}: {main_name}")
        model_path = folder / main_name
        model_path.write_bytes(request_bytes(gltf_file["url"], 40_000_000))
        includes = gltf_file.get("include", {})
        for relative_name, file_info in includes.items():
            relative_path = safe_relative_path(relative_name)
            target = folder / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(request_bytes(file_info["url"], 40_000_000))
        thumb_url = metadata.get("thumbnail_url", "")
        if not thumb_url:
            raise ValueError(f"Missing Poly Haven preview for {asset_id}")
        parsed = urllib.parse.urlparse(thumb_url)
        query = dict(urllib.parse.parse_qsl(parsed.query))
        query.update({"width": "768", "height": "768", "format": "jpg"})
        preview_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))
        preview_path = folder / "preview.jpg"
        save_jpeg(request_bytes(preview_url), preview_path, 768)
        entries.append({
            "id": f"model.{asset_id}", "title": title,
            "description": metadata.get("description", ""),
            "path": "res://" + model_path.relative_to(ROOT).as_posix(),
            "preview_path": "res://" + preview_path.relative_to(ROOT).as_posix(),
            "kind": "3d", "category": "Naturaleza y utilería realista",
            "format": model_path.suffix.lstrip(".").upper(),
            "polycount": polycount, "dimensions_mm": metadata.get("dimensions", []),
            "license": "CC0-1.0", "source": f"https://polyhaven.com/a/{asset_id}",
            "publisher": "Poly Haven", "authors": metadata.get("authors", {}),
            "tags": metadata.get("tags", []), "sha256": sha256(model_path),
            "offline": True, "placeable": True,
        })
    return entries


def main() -> None:
    api_assets = get_json("https://api.polyhaven.com/assets")
    entries = build_2d(api_assets) + build_3d(api_assets)
    catalog = {
        "schemaVersion": 2,
        "catalogId": "jedl_offline_realistic_assets_v1",
        "licensePolicy": {"allowed": ["CC0-1.0"], "redistribution": True},
        "attribution": "Photographic and 3D assets supplied by Poly Haven (CC0).",
        "assets": entries,
    }
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    count_2d = sum(item["kind"] == "2d" for item in entries)
    count_3d = sum(item["kind"] == "3d" for item in entries)
    assert count_2d == len(HDRIS) and count_3d == len(MODELS)
    print(f"POLYHAVEN_BANK_OK: photoreal_2d={count_2d} realistic_3d={count_3d} license=CC0-1.0")
    print(f"CATALOG_SHA256={sha256(CATALOG)}")


if __name__ == "__main__":
    main()
