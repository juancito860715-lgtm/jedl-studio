extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")
const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var manager = CatalogManagerScript.new()
    root.add_child(manager)

    var entries_2d: Array[Dictionary] = manager.scan_catalog("2d")
    assert(entries_2d.size() >= 222, "The 2D gallery must expose character pieces and object banks")
    var character_entries: Array[Dictionary] = entries_2d.filter(
        func(item: Dictionary) -> bool: return item["category"] == "Personaje"
    )
    assert(character_entries.size() == 42, "The 2D gallery must expose all 42 original rig pieces")
    var object_entries: Array[Dictionary] = entries_2d.filter(
        func(item: Dictionary) -> bool: return item["category"] != "Personaje"
    )
    assert(object_entries.size() >= 180, "The 2D gallery must contain the verified CC0 object and foliage banks")
    assert(entries_2d.all(func(item: Dictionary) -> bool: return item["kind"] == "2d"),
        "All 2D gallery entries must be classified as 2D")

    var models: Array[Dictionary] = manager.scan_catalog("3d")
    assert(models.size() >= 1, "The packaged 3D gallery must expose at least one model")
    assert(models.any(func(item: Dictionary) -> bool:
        return String(item["path"]).ends_with("Fox.glb")
    ), "The 3D gallery must discover the animated Fox GLB fixture")

    var world := Node3D.new()
    root.add_child(world)
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    assert(parser.add_catalog_asset(String(character_entries[0]["path"])),
        "The scene engine must place a selected 2D PNG from the gallery")
    assert(parser.active_instances.back() is Sprite3D,
        "A selected 2D PNG must become a Sprite3D scene instance")
    assert(parser.add_catalog_asset(String(models[0]["path"])),
        "The scene engine must place a selected 3D GLB from the gallery")
    assert(parser.active_instances.back() is Node3D,
        "A selected 3D model must become a Node3D scene instance")

    parser.queue_free()
    world.queue_free()
    manager.queue_free()
    print("CATALOG_MANAGER_TEST_OK")
    quit(0)
