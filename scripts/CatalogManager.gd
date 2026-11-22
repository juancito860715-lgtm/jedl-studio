extends Node
class_name CatalogManager

signal catalog_updated(category: String, entries: Array[Dictionary])

const CATALOG_PATH := "res://assets/gallery/catalog.json"
const MANIFEST_PATH := "res://assets/gallery/manifest.json"

var _catalog_loaded := false
var _catalog_error := ""
var _entries_by_id: Dictionary = {}
var _manifest_by_id: Dictionary = {}
var _all_entries: Array[Dictionary] = []


func load_catalog() -> bool:
    if _catalog_loaded:
        return true
    _catalog_loaded = false
    _catalog_error = ""
    _entries_by_id.clear()
    _manifest_by_id.clear()
    _all_entries.clear()

    var catalog_value: Variant = _read_json(CATALOG_PATH)
    if typeof(catalog_value) != TYPE_DICTIONARY:
        return _fail("Asset catalog is missing or invalid: " + CATALOG_PATH)
    var manifest_value: Variant = _read_json(MANIFEST_PATH)
    if typeof(manifest_value) != TYPE_DICTIONARY:
        return _fail("Offline root manifest is missing or invalid: " + MANIFEST_PATH)

    var catalog: Dictionary = catalog_value
    var manifest: Dictionary = manifest_value
    if int(catalog.get("schemaVersion", -1)) != 2:
        return _fail("Unsupported asset catalog schema")
    if int(manifest.get("schemaVersion", -1)) != 1:
        return _fail("Unsupported offline manifest schema")
    if String(manifest.get("catalogPath", "")) != CATALOG_PATH:
        return _fail("Root manifest points to a different catalog")
    var expected_catalog_hash := String(manifest.get("catalogSha256", ""))
    var actual_catalog_hash := FileAccess.get_sha256(CATALOG_PATH)
    if expected_catalog_hash.is_empty() or actual_catalog_hash != expected_catalog_hash:
        return _fail("Catalog SHA-256 does not match the offline root manifest")

    var manifest_assets: Variant = manifest.get("assets", [])
    var manifest_files: Variant = manifest.get("files", [])
    if typeof(manifest_assets) != TYPE_ARRAY or typeof(manifest_files) != TYPE_ARRAY:
        return _fail("Offline manifest assets/files must be arrays")
    if int(manifest.get("assetCount", -1)) != manifest_assets.size():
        return _fail("Offline manifest assetCount is inconsistent")
    if int(manifest.get("fileCount", -1)) != manifest_files.size():
        return _fail("Offline manifest fileCount is inconsistent")

    for file_value in manifest_files:
        if typeof(file_value) != TYPE_DICTIONARY:
            return _fail("Offline manifest contains an invalid file record")
        var file_record: Dictionary = file_value
        var file_path := String(file_record.get("path", ""))
        var file_hash := String(file_record.get("sha256", ""))
        if not file_path.begins_with("res://") or file_hash.length() != 64:
            return _fail("Offline manifest contains an invalid path or SHA-256")
        if int(file_record.get("sizeBytes", 0)) <= 0:
            return _fail("Offline manifest contains an empty file record: " + file_path)

    for asset_value in manifest_assets:
        if typeof(asset_value) != TYPE_DICTIONARY:
            return _fail("Offline manifest contains an invalid asset record")
        var asset: Dictionary = asset_value
        var asset_id := String(asset.get("assetId", ""))
        if asset_id.is_empty() or _manifest_by_id.has(asset_id):
            return _fail("Offline manifest has a missing or duplicate assetId")
        if not String(asset.get("path", "")).begins_with("res://"):
            return _fail("Offline manifest has an invalid asset path: " + asset_id)
        if String(asset.get("sha256", "")).length() != 64:
            return _fail("Offline manifest has an invalid asset hash: " + asset_id)
        if String(asset.get("license", "")).is_empty():
            return _fail("Offline manifest has no license evidence: " + asset_id)
        if asset.get("offline", false) != true or asset.get("placeable", false) != true:
            return _fail("Offline manifest asset is not marked offline/placeable: " + asset_id)
        _manifest_by_id[asset_id] = asset.duplicate(true)

    var catalog_assets: Variant = catalog.get("assets", [])
    if typeof(catalog_assets) != TYPE_ARRAY or catalog_assets.is_empty():
        return _fail("Asset catalog has no assets")
    for entry_value in catalog_assets:
        if typeof(entry_value) != TYPE_DICTIONARY:
            return _fail("Asset catalog contains an invalid entry")
        var entry: Dictionary = entry_value
        var asset_id := String(entry.get("id", ""))
        if asset_id.is_empty() or _entries_by_id.has(asset_id):
            return _fail("Asset catalog has a missing or duplicate id")
        var manifest_entry: Dictionary = _manifest_by_id.get(asset_id, {})
        if manifest_entry.is_empty():
            return _fail("Asset is absent from the root manifest: " + asset_id)
        if String(entry.get("path", "")) != String(manifest_entry.get("path", "")):
            return _fail("Asset path differs from root manifest: " + asset_id)
        if String(entry.get("sha256", "")) != String(manifest_entry.get("sha256", "")):
            return _fail("Asset SHA-256 differs from root manifest: " + asset_id)
        if String(entry.get("license", "")) != String(manifest_entry.get("license", "")):
            return _fail("Asset license differs from root manifest: " + asset_id)
        if entry.get("offline", false) != true or entry.get("placeable", false) != true:
            return _fail("Asset is not marked offline/placeable: " + asset_id)
        _entries_by_id[asset_id] = entry.duplicate(true)
        _all_entries.append(entry.duplicate(true))

    if _entries_by_id.size() != _manifest_by_id.size():
        return _fail("Catalog and root manifest asset counts differ")
    _catalog_loaded = true
    return true


func resolve_asset_id(asset_id: String) -> Dictionary:
    if asset_id.is_empty() or not load_catalog():
        return {}
    var entry: Dictionary = _entries_by_id.get(asset_id, {})
    var manifest_entry: Dictionary = _manifest_by_id.get(asset_id, {})
    if entry.is_empty() or manifest_entry.is_empty():
        return {}
    var resource_path := String(entry.get("path", ""))
    if not _resource_exists(resource_path):
        push_error("Catalog resource is missing: " + resource_path)
        return {}
    # File hashes are audited during the build and recorded in the root manifest.
    # Avoid re-hashing large GLB files on every gallery selection on low-memory phones.
    return entry.duplicate(true)


func scan_catalog(kind: String, category_filter: String = "") -> Array[Dictionary]:
    var entries: Array[Dictionary] = []
    if not load_catalog():
        return entries
    for source_entry in _all_entries:
        if String(source_entry.get("kind", "")) != kind:
            continue
        if not category_filter.is_empty() and String(source_entry.get("category", "")) != category_filter:
            continue
        var resource_path := String(source_entry.get("path", ""))
        if resource_path.is_empty() or not _resource_exists(resource_path):
            push_warning("Catalog resource missing from exported project: " + resource_path)
            continue
        var preview_path := String(source_entry.get("preview_path", ""))
        if not preview_path.is_empty() and not _resource_exists(preview_path):
            push_warning("Catalog preview missing from exported project: " + preview_path)
            continue
        entries.append(source_entry.duplicate(true))
    entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return String(a.get("title", "")).nocasecmp_to(String(b.get("title", ""))) < 0
    )
    catalog_updated.emit(kind, entries)
    return entries


func _resource_exists(path: String) -> bool:
    return not path.is_empty() and (ResourceLoader.exists(path) or FileAccess.file_exists(path))


func _read_json(path: String) -> Variant:
    if not FileAccess.file_exists(path):
        return null
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return null
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    file.close()
    return parsed


func _fail(message: String) -> bool:
    _catalog_error = message
    _catalog_loaded = false
    _entries_by_id.clear()
    _manifest_by_id.clear()
    _all_entries.clear()
    push_error(message)
    return false
