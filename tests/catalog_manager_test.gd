extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var manager = CatalogManagerScript.new()
    root.add_child(manager)

    var character_parts: Array[Dictionary] = manager.scan_catalog(
        "res://assets/gallery/2d/characters/jedl_master_v1/png"
    )
    assert(character_parts.size() == 42, "The 2D character gallery must expose all 42 original rig pieces")
    assert(character_parts.all(func(item: Dictionary) -> bool: return item["kind"] == "2d"),
        "PNG character parts must be classified as 2D")

    var objects: Array[Dictionary] = manager.scan_catalog("res://assets/gallery/2d/objects")
    assert(objects.size() >= 180, "The 2D object gallery must contain the verified CC0 object and foliage banks")
    assert(objects.all(func(item: Dictionary) -> bool: return item["extension"] == "png"),
        "The 2D object gallery must contain image assets only")

    var models: Array[Dictionary] = manager.scan_catalog("res://assets/characters")
    assert(models.any(func(item: Dictionary) -> bool:
        return item["kind"] == "3d" and String(item["path"]).ends_with("Fox.glb")
    ), "The 3D gallery must discover the animated Fox GLB fixture")

    manager.queue_free()
    print("CATALOG_MANAGER_TEST_OK")
    quit(0)
