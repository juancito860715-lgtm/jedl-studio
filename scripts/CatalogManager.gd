extends Node
class_name CatalogManager

signal catalog_updated(category: String, entries: Array[Dictionary])

const CATALOG_PATH := "res://assets/gallery/catalog.json"


func scan_catalog(kind: String, category_filter: String = "") -> Array[Dictionary]:
    var entries: Array[Dictionary] = []
    var file := FileAccess.open(CATALOG_PATH, FileAccess.READ)
    if file == null:
        push_error("Asset catalog manifest could not be opened: " + CATALOG_PATH)
        return entries
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    file.close()
    if not parsed is Dictionary or not parsed.get("assets", []) is Array:
        push_error("Asset catalog manifest has an invalid structure")
        return entries
    for raw_entry in parsed["assets"]:
        if not raw_entry is Dictionary or String(raw_entry.get("kind", "")) != kind:
            continue
        if not category_filter.is_empty() and String(raw_entry.get("category", "")) != category_filter:
            continue
        var entry: Dictionary = raw_entry.duplicate(true)
        var resource_path := String(entry.get("path", ""))
        if resource_path.is_empty() or not ResourceLoader.exists(resource_path):
            push_warning("Catalog resource missing from exported project: " + resource_path)
            continue
        entries.append(entry)
    entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return String(a.get("title", "")).nocasecmp_to(String(b.get("title", ""))) < 0
    )
    catalog_updated.emit(kind, entries)
    return entries
