#!/usr/bin/env python3
"""Build an offline, license-audited photorealistic Poly Haven asset bank.

Downloads are pinned to a small curated allowlist. The Android app never calls
Poly Haven at runtime: all selected assets and metadata are packaged locally.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.parse
import urllib.request
import urllib.error
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT_3D = ROOT / "assets/gallery/3d"
CATALOG = ROOT / "assets/gallery/catalog.json"
USER_AGENT = "JEDL-Studio-Offline-Asset-Builder/1.0 (CC0 asset packaging)"
POLYHAVEN_LICENSE = "https://polyhaven.com/license"

MODELS = {
    "tree_stump_01": ("Tocón de árbol con musgo", "Árboles y vegetación"),
    "tree_stump_02": ("Tocón de árbol envejecido", "Árboles y vegetación"),
    "dead_quiver_branch_01": ("Rama seca de bosque", "Rocas y troncos"),
    "dead_quiver_branch_02": ("Tronco caído erosionado", "Rocas y troncos"),
    "dead_quiver_trunk": ("Tronco natural", "Rocas y troncos"),
    "dead_tree_trunk_02": ("Tronco caído con líquenes", "Rocas y troncos"),
    "ArmChair_01": ("Sillón de madera tallada", "Mobiliario"),
    "Barrel_02": ("Barril industrial azul", "Contenedores y utilería"),
    "treasure_chest": ("Cofre de madera antiguo", "Contenedores y utilería"),
    "tool_cart": ("Carro de herramientas", "Mobiliario"),
    "trashbag": ("Bolsa de residuos", "Contenedores y utilería"),
}


def request_bytes(url: str, max_bytes: int = 80_000_000) -> bytes:
    if urllib.parse.urlparse(url).scheme != "https":
        raise ValueError(f"Asset downloads must use HTTPS: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read(max_bytes + 1)
            if not payload or len(payload) > max_bytes:
                raise ValueError(f"Download size invalid for {url}: {len(payload)} bytes")
            return payload
        except urllib.error.HTTPError as error:
            if error.code < 500 and error.code != 429:
                raise
            last_error = error
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
        if attempt < 4:
            time.sleep(min(2 ** attempt, 12))
    raise RuntimeError(f"Download failed after five attempts: {url}") from last_error


def verify_provider_license(metadata: dict, asset_id: str) -> None:
    declared = metadata.get("license")
    if declared is not None and str(declared).strip().upper() not in {"CC0", "CC0-1.0"}:
        raise ValueError(f"Poly Haven API reports a non-CC0 license for {asset_id}: {declared}")


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
    normalized = value.replace("\\", "/")
    path = Path(normalized)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Unsafe model include path: {value}")
    return path


def build_2d(api_assets: dict) -> list[dict]:
    """Full-frame photographic backgrounds are intentionally excluded from JEDL."""
    return []


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
    for asset_id, model_data in MODELS.items():
        title, category = model_data
        metadata = api_assets.get(asset_id)
        if not metadata or metadata.get("type") != 2:
            raise ValueError(f"Missing or invalid Poly Haven model: {asset_id}")
        verify_provider_license(metadata, asset_id)
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
        query.update({"width": "768", "height": "768", "format": "webp"})
        preview_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))
        preview_path = folder / "preview.jpg"
        save_jpeg(request_bytes(preview_url), preview_path, 768)
        entries.append({
            "id": f"model.{asset_id}", "title": title,
            "description": metadata.get("description", ""),
            "path": "res://" + model_path.relative_to(ROOT).as_posix(),
            "preview_path": "res://" + preview_path.relative_to(ROOT).as_posix(),
            "kind": "3d", "category": category,
            "format": model_path.suffix.lstrip(".").upper(),
            "polycount": polycount, "dimensions_mm": metadata.get("dimensions", []),
            "license": "CC0-1.0", "licenseEvidence": POLYHAVEN_LICENSE, "source": f"https://polyhaven.com/a/{asset_id}",
            "publisher": "Poly Haven", "authors": metadata.get("authors", {}),
            "tags": metadata.get("tags", []), "sha256": sha256(model_path),
            "offline": True, "placeable": True,
        })
    return entries


def main() -> None:
    api_assets = get_json("https://api.polyhaven.com/assets")
    entries = build_3d(api_assets)
    fox_path = ROOT / "assets/characters/Fox.glb"
    if not fox_path.is_file():
        raise FileNotFoundError("The Khronos Fox GLB test character was not downloaded")
    fox_license = ROOT / "assets/characters/Fox.LICENSE.md"
    if not fox_license.is_file():
        raise FileNotFoundError("The Khronos Fox license file was not downloaded")
    fox_license_text = fox_license.read_text(encoding="utf-8")
    if "CC0-1.0" not in fox_license_text or "CC-BY-4.0" not in fox_license_text:
        raise ValueError("The Khronos Fox license file does not contain the expected CC0 and CC-BY grants")
    entries.append({
        "id": "character.fox.khronos.v1", "title": "Zorro animado · Walk / Run",
        "description": "Personaje 3D riggeado de muestra con animaciones Walk, Run y Survey",
        "path": "res://" + fox_path.relative_to(ROOT).as_posix(),
        "kind": "3d", "category": "Personajes animados",
        "format": "GLB", "license": "CC0-1.0 + CC-BY-4.0",
        "licenseEvidence": "https://github.com/KhronosGroup/glTF-Sample-Assets/blob/main/Models/Fox/LICENSE.md",
        "licenseFile": "res://assets/characters/Fox.LICENSE.md",
        "attribution": "Khronos glTF Sample Assets contributors",
        "source": "https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Fox",
        "publisher": "Khronos glTF Sample Assets",
        "offline": True, "placeable": True,
    })
    catalog = {
        "schemaVersion": 2,
        "catalogId": "jedl_offline_realistic_assets_v1",
        "licensePolicy": {"allowed": ["CC0-1.0", "CC-BY-4.0"], "redistribution": True},
        "attribution": "Poly Haven assets are CC0. The Khronos Fox sample is CC-BY-4.0; attribution is included in its source package.",
        "assets": entries,
    }
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count_2d = sum(item["kind"] == "2d" for item in entries)
    count_3d = sum(item["kind"] == "3d" for item in entries)
    assert count_2d == 0 and count_3d == len(MODELS) + 1
    print(f"POLYHAVEN_BANK_OK: photographic_backgrounds_removed={count_2d} realistic_3d_assets={count_3d} license=CC0-1.0")
    print(f"CATALOG_SHA256={sha256(CATALOG)}")


if __name__ == "__main__":
    main()
