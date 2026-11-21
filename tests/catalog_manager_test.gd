extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")
const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var manager = CatalogManagerScript.new()
    root.add_child(manager)

    var character_parts: Array[Dictionary] = manager.scan_catalog(
        "2d"
    )
    assert(character_parts.size() >= 222, "The 2D gallery must expose character pieces and object banks")
    var character_entries := character_parts.filter(func(item: Dictionary) -> bool: return item["category"] == "Personaje")
    assert(character_entries.size() == 42, "The 2D gallery must expose all 42 original rig pieces")
    assert(character_parts.all(func(item: Dictionary) -> bool: return item["kind"] == "2d"),
        "PNG character parts must be classified as 2D")

    var objects: Array[Dictionary] = manager.scan_catalog("2d")
    var objects := character_parts.filter(func(item: Dictionary) -> bool: return item["category"] != "Personaje")
    assert(objects.size() >= 180, "The 2D object gallery must contain the verified CC0 object and foliage banks")
    assert(objects.all(func(item: Dictionary) -> bool: return item["extension"] == "png"),
        "The 2D object gallery must contain image assets only")

    var world := Node3D.new()
    root.add_child(world)
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    assert(parser.add_catalog_asset(String(character_parts[0]["path"])),
        "The scene engine must place a selected 2D PNG from the gallery")
    assert(parser.active_instances.back() is Sprite3D,
        "A selected 2D PNG must become a Sprite3D scene instance")
    assert(parser.add_catalog_asset("3d/Fox.glb"),
        "The scene engine must place a selected 3D GLB from the gallery")
    assert(parser.active_instances.back() is Node3D,
        "A selected 3D model must become a Node3D scene instance")

    var models: Array[Dictionary] = manager.scan_catalog("res://assets/characters")
    assert(models.any(func(item: Dictionary) -> bool:
        return String(item["path"]).ends_with("Fox.glb")
    ), "The 3D gallery must discover the animated Fox GLB fixture")

    parser.queue_free()
    world.queue_free()
    manager.queue_free()
    print("CATALOG_MANAGER_TEST_OK")
    quit(0)
