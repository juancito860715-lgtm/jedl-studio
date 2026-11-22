extends SceneTree

const CATALOG_PATH := "res://assets/gallery/catalog.json"
const REPORT_PATH := "res://assets/gallery/validation_report.json"


func _initialize() -> void:
    call_deferred("_run_validation")


func _run_validation() -> void:
    var catalog_file := FileAccess.open(CATALOG_PATH, FileAccess.READ)
    if catalog_file == null:
        push_error("CATALOG_ASSET_VALIDATION_FAILED: catalog.json is missing")
        quit(1)
        return
    var parsed: Variant = JSON.parse_string(catalog_file.get_as_text())
    catalog_file.close()
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("CATALOG_ASSET_VALIDATION_FAILED: catalog schema is invalid")
        quit(1)
        return
    var catalog: Dictionary = parsed
    if typeof(catalog.get("assets", null)) != TYPE_ARRAY:
        push_error("CATALOG_ASSET_VALIDATION_FAILED: catalog assets are not an array")
        quit(1)
        return

    var report := {
        "schemaVersion": 1,
        "engine": "Godot 4.4.1",
        "catalogSha256": FileAccess.get_sha256(CATALOG_PATH),
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
        var record := {
            "assetId": asset_id,
            "path": resource_path,
            "kind": String(entry.get("kind", "")),
            "importado": false,
            "instanciado": false,
            "renderizable": false,
            "meshInstances": 0,
            "surfaces": 0,
            "errors": [],
        }

        var resource := ResourceLoader.load(resource_path)
        if resource == null:
            record["errors"].append("ResourceLoader.load returned null")
        else:
            record["importado"] = true
            if record["kind"] == "3d":
                if not resource is PackedScene:
                    record["errors"].append("3D resource is not a PackedScene")
                else:
                    var instance: Node = (resource as PackedScene).instantiate()
                    if instance == null:
                        record["errors"].append("PackedScene.instantiate returned null")
                    else:
                        root.add_child(instance)
                        await process_frame
                        record["instanciado"] = true
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
                            var count := mesh_instance.mesh.get_surface_count()
                            if count <= 0:
                                continue
                            var bounds := mesh_instance.mesh.get_aabb()
                            if bounds.size.length() <= 0.0001:
                                continue
                            valid_meshes += 1
                            surface_total += count
                        record["meshInstances"] = valid_meshes
                        record["surfaces"] = surface_total
                        record["renderizable"] = valid_meshes > 0 and surface_total > 0
                        if not record["renderizable"]:
                            record["errors"].append("No MeshInstance3D with non-empty surfaces and bounds")
                        instance.queue_free()
                        await process_frame
            elif record["kind"] == "2d":
                if resource is Texture2D:
                    var texture := resource as Texture2D
                    record["instanciado"] = texture.get_width() > 0 and texture.get_height() > 0
                    record["renderizable"] = record["instanciado"]
                    if not record["renderizable"]:
                        record["errors"].append("Texture dimensions are empty")
                else:
                    record["errors"].append("2D resource is not a Texture2D")
            else:
                record["errors"].append("Unsupported catalog kind")

        var preview_path := String(entry.get("preview_path", ""))
        if not preview_path.is_empty():
            var preview := ResourceLoader.load(preview_path)
            if not preview is Texture2D:
                record["errors"].append("Preview failed to load as Texture2D")
                record["renderizable"] = false

        if not record["importado"] or not record["instanciado"] or not record["renderizable"] or not record["errors"].is_empty():
            failed = true
            push_error("ASSET_VALIDATION_FAILED: " + asset_id + " " + JSON.stringify(record["errors"]))
        report["assets"].append(record)

    var report_file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if report_file == null:
        push_error("CATALOG_ASSET_VALIDATION_FAILED: cannot write validation_report.json")
        quit(1)
        return
    report_file.store_string(JSON.stringify(report, "\t") + "\n")
    report_file.close()

    if failed or report["assets"].size() != report["assetCount"]:
        push_error("CATALOG_ASSET_VALIDATION_FAILED: one or more catalog resources failed")
        quit(1)
        return
    print("CATALOG_ASSET_VALIDATION_OK: assets=%d" % report["assetCount"])
    quit(0)
