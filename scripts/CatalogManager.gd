extends Node
class_name CatalogManager

signal catalog_updated(category: String, entries: Array[Dictionary])


func scan_catalog(folder_path: String) -> Array[Dictionary]:
    var entries: Array[Dictionary] = []
    _scan_directory(folder_path, folder_path, entries)
    entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return String(a.get("title", "")).nocasecmp_to(String(b.get("title", ""))) < 0
    )
    catalog_updated.emit(folder_path, entries)
    return entries


func _scan_directory(root_path: String, current_path: String, entries: Array[Dictionary]) -> void:
    var directory := DirAccess.open(current_path)
    if directory == null:
        return
    directory.list_dir_begin()
    var item := directory.get_next()
    while item != "":
        if item.begins_with("."):
            item = directory.get_next()
            continue
        var full_path := current_path.path_join(item)
        if directory.current_is_dir():
            _scan_directory(root_path, full_path, entries)
        elif item.get_extension().to_lower() in ["glb", "gltf", "tscn"]:
            entries.append({
                "id": item.get_basename(),
                "title": item.get_basename().replace("_", " ").capitalize(),
                "path": full_path,
                "category": full_path.trim_prefix(root_path).trim_prefix("/")
            })
        item = directory.get_next()
    directory.list_dir_end()
