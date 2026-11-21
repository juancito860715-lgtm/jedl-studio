extends Node
class_name CatalogManager

signal catalog_updated(category: String, entries: Array[Dictionary])

const IMAGE_EXTENSIONS := ["png", "jpg", "jpeg", "webp"]
const MODEL_EXTENSIONS := ["glb", "gltf", "tscn"]


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
        else:
            var extension := item.get_extension().to_lower()
            if extension in IMAGE_EXTENSIONS or extension in MODEL_EXTENSIONS:
                var relative_path := full_path.trim_prefix(root_path).trim_prefix("/")
                var kind := "2d" if extension in IMAGE_EXTENSIONS else "3d"
                entries.append({
                    "id": relative_path.to_lower().replace("/", ":"),
                    "title": item.get_basename().replace("_", " ").replace("-", " ").capitalize(),
                    "path": full_path,
                    "relative_path": relative_path,
                    "category": relative_path.get_base_dir(),
                    "kind": kind,
                    "extension": extension
                })
        item = directory.get_next()
    directory.list_dir_end()
