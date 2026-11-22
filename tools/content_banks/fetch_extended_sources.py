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


def fetch(url: str, limit: int, headers: dict[str, str] | None = None) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"HTTPS URL required: {url}")
    request_headers = {"User-Agent": UA}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers)
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


def get_json(url: str, limit: int = 20_000_000, headers: dict[str, str] | None = None) -> dict:
    value = json.loads(fetch(url, limit, headers=headers).decode("utf-8"))
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


def require_preview_url(preview_url: str, asset_id: str) -> str:\n    """Reject 3D entries that cannot produce an offline gallery thumbnail."""\n    if not preview_url or not preview_url.startswith("https://"):\n        raise ValueError(f"Every 3D model must provide an HTTPS preview URL: {asset_id}")\n    return preview_url\n\n\ndef add_model(entries: list[dict], *, asset_id: str, title: str, category: str,
              provider: str, source: str, license_url: str, license_id: str,
              model_url: str, license_payload: bytes | None = None,
              preview_url: str = "", description: str = "") -> None:
    if license_id != "CC0-1.0":
        raise ValueError(f"Non-CC0 item is not accepted by the default catalog: {asset_id}")
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
              license_payload=None,
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
        category_key = str(model.get("category", "")).lower()
        if not any(token in category_key for token in ("character", "animal", "nature", "building", "furniture", "prop")):
            continue
        style = str(model.get("style", "")).lower()
        if style != "realistic":
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


def add_art_institute_photographs(entries: list[dict]) -> None:
    # Art Institute data is CC0, but only photographic works are admitted.
    query = urllib.parse.urlencode({
        "q": "photograph",
        "query[term][is_public_domain]": "true",
        "limit": "8",
        "fields": "id,title,artist_display,date_display,image_id,artwork_type_title,classification_title,is_public_domain"
    })
    url = "https://api.artic.edu/api/v1/artworks/search?" + query
    aic_headers = {"AIC-User-Agent": "JEDL-Studio-Offline-Asset-Builder/1.0"}
    result = get_json(url, 8_000_000, headers=aic_headers)
    records = result.get("data", [])
    iiif_base = str(result.get("config", {}).get("iiif_url", "")).rstrip("/")
    if not iiif_base.startswith("https://"):
        raise ValueError("Art Institute API did not provide a valid HTTPS IIIF base URL")
    from PIL import Image
    import io
    for item in records:
        if item.get("is_public_domain") is not True or not item.get("image_id"):
            continue
        type_name = str(item.get("artwork_type_title", "")).lower()
        classification = str(item.get("classification_title", "")).lower()
        if "photograph" not in type_name and "photograph" not in classification:
            continue
        # Verify item-level rights before requesting the image binary.
        detail_url = f"https://api.artic.edu/api/v1/artworks/{item['id']}"
        detail = get_json(detail_url, 2_000_000, headers=aic_headers)
        rights_record = detail.get("data", {})
        cc0_url = "https://creativecommons.org/publicdomain/zero/1.0/"
        license_links = detail.get("info", {}).get("license_links", [])
        if rights_record.get("is_public_domain") is not True or cc0_url not in license_links:
            continue
        image_id = str(item["image_id"])
        image_url = f"{iiif_base}/{image_id}/full/843,/0/default.jpg"
        payload = fetch(image_url, MAX_IMAGE_BYTES, headers=aic_headers)
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
        rights_path = folder / f"aic_{item['id']}.rights.json"
        rights_path.write_text(json.dumps({
            "record": rights_record,
            "license": "CC0-1.0",
            "licenseLinks": license_links,
            "sourceApi": detail_url
        }, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        entries.append({
            "id": f"background.aic.photograph.{item['id']}",
            "title": str(item.get("title", "Historical photograph")),
            "description": f"{item.get('artist_display', '')} · {item.get('date_display', '')}",
            "path": "res://" + path.relative_to(ROOT).as_posix(),
            "preview_path": "res://" + path.relative_to(ROOT).as_posix(),
            "kind": "2d", "category": "Fondos fotográficos",
            "format": "JPEG", "width": image.width, "height": image.height,
            "license": "CC0-1.0", "licenseEvidence": f"https://api.artic.edu/api/v1/artworks/{item['id']}",
            "licenseFile": "res://" + rights_path.relative_to(ROOT).as_posix(),
            "source": f"https://www.artic.edu/artworks/{item['id']}",
            "publisher": "Art Institute of Chicago",
            "sha256": digest(path), "offline": True, "placeable": True
        })
        time.sleep(1.0)


def run_optional_source(source_name: str, operation, statuses: list[dict]) -> None:
    """Run a non-core provider without hiding its failure or blocking verified feeds."""
    try:
        operation()
        statuses.append({"source": source_name, "status": "completed"})
        print(f"OPTIONAL_SOURCE_OK: {source_name}")
    except Exception as error:
        status = {"source": source_name, "status": "deferred", "error_type": type(error).__name__, "reason": str(error)}
        statuses.append(status)
        print(f"OPTIONAL_SOURCE_DEFERRED: {source_name}: {type(error).__name__}: {error}")

def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    entries = catalog.get("assets", [])
    existing = {item["id"] for item in entries}
    additions: list[dict] = []
    # Provider-specific errors are not silently swallowed: CI fails with the source and item.
    add_tevy(additions)
    add_grab3d(additions)
    # Other catalog feeds remain disabled until their import format passes
    # the Godot 4.4 importer and the per-item redistribution evidence gate.
    optional_statuses: list[dict] = []
    run_optional_source(
        "Art Institute of Chicago photographic backgrounds",
        lambda: add_art_institute_photographs(additions),
        optional_statuses,
    )
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
    print("OPTIONAL_SOURCE_STATUS: " + json.dumps(optional_statuses, ensure_ascii=False))
    print("SOURCE_STATUS: Smithsonian and NASA held until item-level CC0/public-domain media proof is attached; "
          "Rijksmuseum held until an authenticated or openly accessible image endpoint and item rights record "
          "are verified; other compressed feeds remain held until Godot 4.4 compatibility is proven; "
          "OmniMod remains outside the realism-first tier because its catalogue is predominantly low-poly/static; "
          "Innerscene human base meshes are not included without a suitable clothed, production-ready model.")


if __name__ == "__main__":
    main()
