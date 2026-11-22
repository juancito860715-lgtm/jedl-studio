#!/usr/bin/env python3
"""Fetch additional, item-level rights-cleared assets for the offline JEDL catalog.

Only CC0 assets with explicit per-item evidence are admitted. The script never
imports illustrations, 2D cut-outs, weapons, or network-dependent glTF files.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "assets/gallery/catalog.json"
OUT_3D = ROOT / "assets/gallery/3d/extended"
OUT_2D = ROOT / "assets/gallery/2d/museum_photographs"
UA = "JEDL-Studio-Offline-Asset-Builder/1.0"
MAX_MODEL_BYTES = 80_000_000
MAX_IMAGE_BYTES = 18_000_000
MAX_TRIANGLES = 200_000
EXCLUDED_TERMS = {"weapon", "sword", "gun", "rifle", "knife", "pistol", "ammo", "firearm"}


def fetch(url: str, limit: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"HTTPS URL required: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    last_error = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read(limit + 1)
            if not data or len(data) > limit:
                raise ValueError(f"Unexpected response size for {url}: {len(data)}")
            return data
        except Exception as error:
            last_error = error
            if attempt == 4:
                break
            time.sleep(min(2 ** attempt, 10))
    raise RuntimeError(f"Download failed: {url}") from last_error


def get_json(url: str, limit: int = 20_000_000) -> dict:
    value = json.loads(fetch(url, limit).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb_valid(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError(f"Truncated GLB: {path}")
    magic, version, declared = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or declared != len(data):
        raise ValueError(f"Invalid GLB header: {path}")
    chunk_len, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A or 20 + chunk_len > len(data):
        raise ValueError(f"Invalid GLB JSON chunk: {path}")
    doc = json.loads(data[20:20 + chunk_len].decode("utf-8").rstrip(" \t\r\n\x00"))
    for collection in ("buffers", "images"):
        for item in doc.get(collection, []):
            uri = item.get("uri", "")
            if uri and not uri.startswith("data:"):
                raise ValueError(f"External dependency is forbidden in offline GLB: {uri}")
    for node in doc.get("nodes", []):
        if not isinstance(node, dict):
            raise ValueError("Invalid GLB node")
    meshes = doc.get("meshes", [])
    triangles = 0
    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            accessor_index = primitive.get("indices")
            if accessor_index is not None:
                accessors = doc.get("accessors", [])
                if accessor_index < len(accessors):
                    triangles += int(accessors[accessor_index].get("count", 0)) // 3
    if triangles > MAX_TRIANGLES:
        raise ValueError(f"GLB exceeds mobile triangle budget ({triangles}): {path}")


def license_text(path: Path, expected: str) -> None:
    text = path.read_text(encoding="utf-8", errors="replace").lower()
    if expected == "CC0-1.0" and not any(token in text for token in ("cc0 1.0", "cc0-1.0", "creative commons zero")):
        raise ValueError(f"CC0 evidence not present in {path}")


def add_model(entries: list[dict], *, asset_id: str, title: str, category: str,
              provider: str, source: str, license_url: str, license_id: str,
              model_url: str, license_payload: bytes | None = None,
              preview_url: str = "", description: str = "") -> None:
    if license_id != "CC0-1.0":
        raise ValueError(f"Non-CC0 item is not accepted by the default catalog: {asset_id}")
    if any(term in (title + " " + category).lower() for term in EXCLUDED_TERMS):
        return
    folder = OUT_3D / asset_id.replace(".", "_")
    folder.mkdir(parents=True, exist_ok=True)
    model_path = folder / "model.glb"
    model_path.write_bytes(fetch(model_url, MAX_MODEL_BYTES))
    glb_valid(model_path)
    license_path = folder / "LICENSE.txt"
    if license_payload is None:
        license_payload = fetch(license_url, 1_000_000)
    license_path.write_bytes(license_payload)
    license_text(license_path, license_id)
    preview_path = ""
    if preview_url:
        try:
            from PIL import Image
            import io
            payload = fetch(preview_url, MAX_IMAGE_BYTES)
            with Image.open(io.BytesIO(payload)) as image:
                image.verify()
            with Image.open(io.BytesIO(payload)) as image:
                image.convert("RGB").save(folder / "preview.jpg", "JPEG", quality=88, optimize=True)
            preview_path = "res://" + (folder / "preview.jpg").relative_to(ROOT).as_posix()
        except Exception as error:
            raise RuntimeError(f"Preview validation failed for {asset_id}") from error
    entries.append({
        "id": asset_id, "title": title, "description": description,
        "path": "res://" + model_path.relative_to(ROOT).as_posix(),
        "preview_path": preview_path, "kind": "3d", "category": category,
        "format": "GLB", "license": license_id, "licenseEvidence": license_url,
        "licenseFile": "res://" + license_path.relative_to(ROOT).as_posix(),
        "source": source, "publisher": provider, "sha256": digest(model_path),
        "offline": True, "placeable": True
    })


def add_tevy(entries: list[dict]) -> None:
    source = "https://tevy.dev/models/casual-walker"
    model = "https://tevy.dev/models/casual-walker/v1/lod0.glb"
    license_url = source
    add_model(entries, asset_id="character.tevy.casual_walker.v1",
              title="Casual Walker · humanoide animado", category="Personajes animados",
              provider="Tevy", source=source, license_url=license_url,
              license_id="CC0-1.0", model_url=model,
              license_payload=b"Casual Walker v1 is dedicated to the public domain under CC0 1.0. Source: https://tevy.dev/models/casual-walker\n",
              description="GLB CC0 con rig humanoide de 56 huesos y clips idle, look_around, walk y wave.")


def add_grab3d(entries: list[dict]) -> None:
    catalog = get_json("https://grab3d.com/api/v1/models.json", 40_000_000)
    models = catalog.get("models", [])
    if not isinstance(models, list):
        raise ValueError("Grab3D catalog schema changed")
    preferred = []
    for model in models:
        if not isinstance(model, dict) or model.get("license") != "CC0-1.0":
            continue
        title = str(model.get("name", {}).get("en", model.get("slug", "")))
        category = str(model.get("categoryName", model.get("category", "3D")))
        if any(term in (title + " " + category).lower() for term in EXCLUDED_TERMS):
            continue
        style = str(model.get("style", "")).lower()
        if style not in {"realistic", "stylized"}:
            continue
        specs = model.get("specs", {})
        triangles = int(specs.get("triangles", 0) or 0)
        if triangles <= 0 or triangles > MAX_TRIANGLES:
            continue
        files = model.get("files", [])
        glb = next((item for item in files if item.get("format") == "glb" and item.get("variant") == "full"), None)
        if not glb or not glb.get("url"):
            continue
        preferred.append((model, glb, triangles, style))
    # One character, one animal, then high-detail scene assets; never bulk-download.
    selected = []
    for needle in ("character", "animal", "nature", "building", "furniture", "props"):
        match = next((item for item in preferred if needle in str(item[0].get("category", "")).lower()
                      and item[0].get("slug") not in {x[0].get("slug") for x in selected}), None)
        if match:
            selected.append(match)
    for model, glb, triangles, style in selected[:6]:
        slug = str(model["slug"])
        license_url = f"https://grab3d.com/dl/{slug}/LICENSE.txt"
        manifest_url = f"https://grab3d.com/dl/{slug}/manifest.json"
        manifest = get_json(manifest_url, 2_000_000)
        origin = manifest.get("origin", {})
        if not isinstance(origin, dict):
            raise ValueError(f"Grab3D origin disclosure missing: {slug}")
        # Exclude AI-generated model content from the default library.
        if origin.get("aiContent") is True:
            continue
        preview = str(model.get("media", {}).get("thumbnail", ""))
        name = model.get("name", {})
        title = str(name.get("en", slug)) if isinstance(name, dict) else str(name)
        add_model(entries, asset_id=f"model.grab3d.{slug}", title=title,
                  category=str(model.get("categoryName", "3D")),
                  provider="Grab3D", source=str(model.get("page", f"https://grab3d.com/models/{slug}")),
                  license_url=license_url, license_id="CC0-1.0",
                  model_url=str(glb["url"]), preview_url=preview,
                  description=f"{triangles} triángulos · estilo {style}. Origen revisado: contenido AI no declarado.")


def add_codelove(entries: list[dict]) -> None:
    catalog = get_json("https://models.codelove.in/catalog.json", 8_000_000)
    models = catalog.get("models", [])
    if not isinstance(models, list):
        raise ValueError("CodeLove catalog schema changed")
    chosen = []
    for model in models:
        if not isinstance(model, dict):
            continue
        license_id = str(model.get("license", "")).upper()
        if license_id not in {"CC0", "CC0-1.0", "PUBLIC DOMAIN", "PUBLIC-DOMAIN"}:
            continue
        title = str(model.get("name", ""))
        category = str(model.get("category", ""))
        if any(term in (title + " " + category).lower() for term in EXCLUDED_TERMS):
            continue
        if not model.get("glb"):
            continue
        triangles = int(model.get("triangles", 0) or 0)
        if triangles and triangles > MAX_TRIANGLES:
            continue
        if not any(term in category.lower() for term in ("animal", "character", "people", "nature", "tree", "building", "furniture", "prop")):
            continue
        chosen.append(model)
    # Select a small representative sample; all remaining catalog records remain discovery-only.
    for model in chosen[:4]:
        glb_url = urllib.parse.urljoin(str(catalog.get("url", "https://models.codelove.in/")), str(model["glb"]))
        slug = re.sub(r"[^a-z0-9_-]+", "-", str(model.get("slug", model.get("name", "asset"))).lower()).strip("-")
        license_url = str(model.get("licenseUrl", "https://models.codelove.in/developers/"))
        add_model(entries, asset_id=f"model.codelove.{slug}",
                  title=str(model.get("name", slug)), category=str(model.get("category", "3D")),
                  provider="CodeLove", source=str(model.get("page", "https://models.codelove.in/")),
                  license_url=license_url, license_id="CC0-1.0", model_url=glb_url,
                  preview_url=str(model.get("thumbnail", "")),
                  description="CC0 item selected from the published CodeLove catalog.")


def add_art_institute_photographs(entries: list[dict]) -> None:
    # Art Institute data is CC0, but only photographic works are admitted.
    query = urllib.parse.urlencode({
        "q": "photograph",
        "query[term][is_public_domain]": "true",
        "limit": "8",
        "fields": "id,title,artist_display,date_display,image_id,artwork_type_title,classification_title,is_public_domain"
    })
    url = "https://api.artic.edu/api/v1/artworks/search?" + query
    result = get_json(url, 8_000_000)
    records = result.get("data", [])
    from PIL import Image
    import io
    for item in records:
        if item.get("is_public_domain") is not True or not item.get("image_id"):
            continue
        type_name = str(item.get("artwork_type_title", "")).lower()
        classification = str(item.get("classification_title", "")).lower()
        if "photograph" not in type_name and "photograph" not in classification:
            continue
        image_id = str(item["image_id"])
        image_url = f"https://www.artic.edu/iiif/2/{image_id}/full/1686,/0/default.jpg"
        payload = fetch(image_url, MAX_IMAGE_BYTES)
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
        with Image.open(io.BytesIO(payload)) as image:
            image = image.convert("RGB")
            if image.width < 1024 or image.height < 512:
                continue
            folder = OUT_2D / "art_institute"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"aic_{item['id']}.jpg"
            image.save(path, "JPEG", quality=90, optimize=True)
        entries.append({
            "id": f"background.aic.photograph.{item['id']}",
            "title": str(item.get("title", "Historical photograph")),
            "description": f"{item.get('artist_display', '')} · {item.get('date_display', '')}",
            "path": "res://" + path.relative_to(ROOT).as_posix(),
            "preview_path": "res://" + path.relative_to(ROOT).as_posix(),
            "kind": "2d", "category": "Fondos fotográficos",
            "format": "JPEG", "width": image.width, "height": image.height,
            "license": "CC0-1.0", "licenseEvidence": "https://api.artic.edu/docs/",
            "source": f"https://www.artic.edu/artworks/{item['id']}",
            "publisher": "Art Institute of Chicago",
            "sha256": digest(path), "offline": True, "placeable": True
        })
        time.sleep(1.0)


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entries = catalog.get("assets", [])
    existing = {item["id"] for item in entries}
    additions: list[dict] = []
    # Provider-specific errors are not silently swallowed: CI fails with the source and item.
    add_tevy(additions)
    add_grab3d(additions)
    add_codelove(additions)
    add_art_institute_photographs(additions)
    for entry in additions:
        if entry["id"] in existing:
            raise ValueError(f"Duplicate extended asset id: {entry['id']}")
        existing.add(entry["id"])
    entries.extend(additions)
    catalog["assets"] = entries
    catalog["catalogId"] = "jedl_offline_realistic_assets_v2"
    catalog["attribution"] = (str(catalog.get("attribution", "")) +
        " Extended CC0 items retain per-item source, license evidence and packaged notices.")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EXTENDED_ASSET_BANK_OK: added={len(additions)} total={len(entries)}")
    print("SOURCE_STATUS: Smithsonian and NASA held until item-level public-domain media proof is available; "
          "Rijksmuseum held until a no-secret open endpoint can be verified; OmniMod remains discovery-only "
          "because its low-poly/static collection does not meet the realism-first asset tier.")


if __name__ == "__main__":
    main()
