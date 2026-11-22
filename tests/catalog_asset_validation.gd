extends SceneTree

const CATALOG_PATH := "res://assets/gallery/catalog.json"
const MANIFEST_PATH := "res://assets/gallery/manifest.json"
const REPORT_PATH := "res://assets/gallery/validation_report.json"


func _initialize() -> void:
    call_deferred("_run_validation")


func _run_validation() -> void:
    var catalog_value: Variant = _read_json(CATALOG_PATH)
    var manifest_value: Variant = _read_json(MANIFEST_PATH)
    if typeof(catalog_value) != TYPE_DICTIONARY:
        _fail("catalog.json is missing or invalid")
        return
    if typeof(manifest_value) != TYPE_DICTIONARY:
        _fail("manifest.json is missing or invalid")
        return

    var catalog: Dictionary = catalog_value
    var manifest: Dictionary = manifest_value
    if typeof(catalog.get("assets", null)) != TYPE_ARRAY:
        _fail("catalog assets are not an array")
        return
    if typeof(manifest.get("assets", null)) != TYPE_ARRAY or typeof(manifest.get("files", null)) != TYPE_ARRAY:
        _fail("manifest assets/files are not arrays")
        return
    if String(manifest.get("catalogPath", "")) != CATALOG_PATH:
        _fail("root manifest points to a different catalog")
        return
    var catalog_hash := FileAccess.get_sha256(CATALOG_PATH)
    if String(manifest.get("catalogSha256", "")) != catalog_hash:
        _fail("root manifest catalog SHA-256 is stale")
        return

    var manifest_assets_by_id: Dictionary = {}
    for asset_value in manifest["assets"]:
        if not asset_value is Dictionary:
            _fail("root manifest contains an invalid asset record")
            return
        var manifest_asset: Dictionary = asset_value
        var manifest_id := String(manifest_asset.get("assetId", ""))
        if manifest_id.is_empty() or manifest_assets_by_id.has(manifest_id):
            _fail("root manifest contains a missing or duplicate assetId")
            return
        manifest_assets_by_id[manifest_id] = manifest_asset

    var files_by_path: Dictionary = {}
    for file_value in manifest["files"]:
        if not file_value is Dictionary:
            _fail("root manifest contains an invalid file record")
            return
        var file_record: Dictionary = file_value
        var file_path := String(file_record.get("path", ""))
        if not file_path.begins_with("res://") or files_by_path.has(file_path):
            _fail("root manifest contains an invalid or duplicate file path")
            return
        files_by_path[file_path] = file_record

    var engine_version_info := Engine.get_version_info()
    var engine_label := "Godot " + String(engine_version_info.get("string", "unknown"))
    var report := {
        "schemaVersion": 2,
        "engine": engine_label,
        "catalogSha256": catalog_hash,
        "assetCount": catalog["assets"].size(),
        "assets": [],
    }
    var failed := false
    for value in catalog["assets"]:
        if not value is Dictionary:
            failed = true
            continue
        var entry: Dictionary = value
        var asset_id := String(entry.get("id", ""))
        var resource_path := String(entry.get("path", ""))
        var kind := String(entry.get("kind", ""))
        var record := {
            "assetId": asset_id,
            "path": resource_path,
            "kind": kind,
            "assetSha256": "",
            "assetSizeBytes": 0,
            "dependencies": [],
            "dependenciesValid": false,
            "importado": false,
            "instanciado": false,
            "renderizable": false,
            "nodeCount": 0,
            "meshInstances": 0,
            "surfaces": 0,
            "errors": [],
        }

        var manifest_asset: Dictionary = manifest_assets_by_id.get(asset_id, {})
        if manifest_asset.is_empty():
            record["errors"].append("Asset is absent from root manifest")
        elif String(manifest_asset.get("path", "")) != resource_path:
            record["errors"].append("Asset path differs from root manifest")
        else:
            var expected_hash := String(manifest_asset.get("sha256", ""))
            var expected_size := int(manifest_asset.get("sizeBytes", -1))
            var file_record: Dictionary = files_by_path.get(resource_path, {})
            if file_record.is_empty():
                record["errors"].append("Asset file is absent from root manifest inventory")
            elif String(file_record.get("sha256", "")) != expected_hash or int(file_record.get("sizeBytes", -1)) != expected_size:
                record["errors"].append("Asset metadata differs between manifest asset and file inventory")
            elif not _file_matches_manifest(resource_path, file_record):
                record["errors"].append("Asset SHA-256 or size differs from root manifest")
            else:
                record["assetSha256"] = expected_hash
                record["assetSizeBytes"] = expected_size
                var dependencies: Variant = manifest_asset.get("dependencies", [])
                var dependencies_valid := dependencies is Array
                if dependencies_valid:
                    for dependency_value in dependencies:
                        var dependency_path := String(dependency_value)
                        var dependency_record: Dictionary = files_by_path.get(dependency_path, {})
                        if dependency_record.is_empty() or not _file_matches_manifest(dependency_path, dependency_record):
                            dependencies_valid = false
                            record["errors"].append("Missing or invalid model dependency: " + dependency_path)
                        else:
                            record["dependencies"].append(dependency_path)
                else:
                    record["errors"].append("Manifest dependencies field is not an array")
                record["dependenciesValid"] = dependencies_valid

        if record["errors"].is_empty():
            if kind == "3d":
                var packed_scene := load(resource_path) as PackedScene
                if packed_scene == null:
                    record["errors"].append("load() did not return a PackedScene")
                else:
                    record["importado"] = true
                    var instance := packed_scene.instantiate()
                    if instance == null:
                        record["errors"].append("PackedScene.instantiate() returned null")
                    else:
                        root.add_child(instance)
                        await process_frame
                        var node_count := _count_descendants(instance)
                        record["nodeCount"] = node_count
                        record["instanciado"] = node_count > 0
                        if node_count <= 0:
                            record["errors"].append("Instantiated PackedScene has zero child nodes")
                        var meshes: Array[MeshInstance3D] = []
                        if instance is MeshInstance3D:
                            meshes.append(instance as MeshInstance3D)
                        for child in instance.find_children("*", "MeshInstance3D", true, false):
                            meshes.append(child as MeshInstance3D)
                        var valid_meshes := 0
                        var surface_total := 0
                        for mesh_instance in meshes:
                            if mesh_instance.mesh == null:
                                continue
                            var surface_count := mesh_instance.mesh.get_surface_count()
                            var bounds := mesh_instance.mesh.get_aabb()
                            if surface_count <= 0 or bounds.size.length() <= 0.0001:
                                continue
                            valid_meshes += 1
                            surface_total += surface_count
                        record["meshInstances"] = valid_meshes
                        record["surfaces"] = surface_total
                        record["renderizable"] = node_count > 0 and valid_meshes > 0 and surface_total > 0
                        if valid_meshes <= 0:
                            record["errors"].append("No MeshInstance3D with non-empty surfaces and bounds")
                        instance.queue_free()
                        await process_frame
            elif kind == "2d":
                var texture := load(resource_path) as Texture2D
                if texture == null:
                    record["errors"].append("load() did not return a Texture2D")
                else:
                    record["importado"] = true
                    var dimensions_valid := texture.get_width() > 0 and texture.get_height() > 0
                    record["instanciado"] = dimensions_valid
                    record["renderizable"] = dimensions_valid
                    if not dimensions_valid:
                        record["errors"].append("Texture dimensions are empty")
            else:
                record["errors"].append("Unsupported catalog kind")

        var preview_path := String(entry.get("preview_path", ""))
        if not preview_path.is_empty():
            var preview := load(preview_path) as Texture2D
            if preview == null or preview.get_width() <= 0 or preview.get_height() <= 0:
                record["errors"].append("Preview failed to load as a non-empty Texture2D")
                record["renderizable"] = false

        if not record["importado"] or not record["instanciado"] or not record["renderizable"] or not record["dependenciesValid"] or not record["errors"].is_empty():
            failed = true
            push_error("ASSET_VALIDATION_FAILED: " + asset_id + " " + JSON.stringify(record["errors"]))
        report["assets"].append(record)

    var report_file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if report_file == null:
        _fail("cannot write validation_report.json")
        return
    report_file.store_string(JSON.stringify(report, "\t") + "\n")
    report_file.close()

    if failed or report["assets"].size() != report["assetCount"] or manifest_assets_by_id.size() != report["assetCount"]:
        _fail("one or more catalog resources failed import, integrity, dependency, instantiation or renderability checks")
        return
    print("CATALOG_ASSET_VALIDATION_OK: assets=%d" % report["assetCount"])
    quit(0)


func _read_json(path: String) -> Variant:
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return null
    var value: Variant = JSON.parse_string(file.get_as_text())
    file.close()
    return value


func _file_matches_manifest(path: String, expected: Dictionary) -> bool:
    if not path.begins_with("res://") or not FileAccess.file_exists(path):
        return false
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return false
    var actual_size := file.get_length()
    file.close()
    var expected_size := int(expected.get("sizeBytes", -1))
    var expected_hash := String(expected.get("sha256", ""))
    if actual_size <= 0 or actual_size != expected_size or expected_hash.length() != 64:
        return false
    return FileAccess.get_sha256(path) == expected_hash


func _count_descendants(node: Node) -> int:
    var count := 0
    for child in node.get_children():
        count += 1 + _count_descendants(child)
    return count


func _fail(message: String) -> void:
    push_error("CATALOG_ASSET_VALIDATION_FAILED: " + message)
    quit(1)
