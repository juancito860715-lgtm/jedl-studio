extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")
const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    _test_engine_identity_matching()
    var manager = CatalogManagerScript.new()
    root.add_child(manager)

    assert(manager.load_catalog(), "Catalog, root manifest and per-asset Godot validation report must agree")
    var resolved_fox: Dictionary = manager.resolve_asset_id("character.fox.khronos.v1")
    assert(not resolved_fox.is_empty(), "Animated 3D character assetId must resolve through the root manifest")

    var entries_2d: Array[Dictionary] = manager.scan_catalog("2d")
    assert(entries_2d.is_empty(), "The catalog must not contain photographic backgrounds or other 2D backplates")

    var models: Array[Dictionary] = manager.scan_catalog("3d")
    assert(models.size() >= 12, "The 3D gallery must expose the curated core models and animated Fox")
    assert(models.any(func(item: Dictionary) -> bool: return item["id"] == "character.fox.khronos.v1"),
        "The animated Fox test character must remain in the gallery")
    for item in models:
        assert(String(item["path"]).ends_with(".gltf") or String(item["path"]).ends_with(".glb"),
            "Every 3D asset must be a real glTF model, not a preview image")
        assert(String(item["license"]).begins_with("CC0-1.0"), "Every 3D model must have verified redistribution rights")
        if item.has("polycount"):
            assert(int(item["polycount"]) <= 200000, "Every model must respect the mobile polygon budget")
        if item.has("preview_path"):
            assert(ResourceLoader.exists(String(item["preview_path"])), "Every 3D model preview must be packaged")

    var world := Node3D.new()
    root.add_child(world)
    var camera := Camera3D.new()
    root.add_child(camera)
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    parser.catalog_manager = manager
    parser.camera = camera
    assert(parser.add_catalog_asset(String(models[0]["path"]), String(models[0]["id"])),
        "The scene engine must place a selected realistic 3D model")
    assert(parser.active_instances.size() == 1 and parser.active_instances.back() is Node3D,
        "A selected 3D model must become a Node3D scene instance")
    var fox_entry: Dictionary = models.filter(func(item: Dictionary) -> bool: return item["id"] == "character.fox.khronos.v1")[0]
    assert(parser.add_catalog_asset(String(fox_entry["path"]), String(fox_entry["id"])),
        "The animated Fox must be placeable from the character gallery")
    var gallery_fox: Node3D = parser.active_instances.back()
    assert(gallery_fox.get_meta("jedl_asset_id") == "character.fox.khronos.v1",
        "Placed Fox must retain its stable assetId")
    var fox_players := gallery_fox.find_children("*", "AnimationPlayer", true, false)
    assert(not fox_players.is_empty(), "The gallery Fox must retain its AnimationPlayer")
    assert((fox_players[0] as AnimationPlayer).is_playing(),
        "Rigged gallery characters must begin their default animation instead of remaining static")
    assert((fox_players[0] as AnimationPlayer).current_animation == "Walk",
        "The Fox gallery default must be the Walk animation")

    parser.queue_free()
    camera.queue_free()
    world.queue_free()
    manager.queue_free()
    print("CATALOG_MANAGER_TEST_OK")
    quit(0)


func _test_engine_identity_matching() -> void:
    var runtime_info := {
        "major": 4,
        "minor": 5,
        "patch": 1,
        "status": "stable",
        "build": "official",
        "hash": "f62fdbde15035c5576dad93e586201f4d41ef0cb",
    }
    assert(CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.official.f62fdbde1", runtime_info
    ), "A CLI-truncated hash that prefixes the runtime hash must match")
    assert(CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.official.f62fdbde15035c5576dad93e586201f4d41ef0cb", runtime_info
    ), "The complete matching build hash must match")
    assert(not CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.2.stable.official.f62fdbde1", runtime_info
    ), "A different patch version must be rejected")
    assert(not CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.official.aaaaaaaaa", runtime_info
    ), "A different build hash must be rejected")
    assert(not CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.custom.f62fdbde1", runtime_info
    ), "A different build channel must be rejected")
    assert(not CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.official.f62fdbde", runtime_info
    ), "A hash shorter than nine characters must be rejected")
    assert(not CatalogManagerScript.engine_identity_matches(
        "Godot 4.5.1.stable.official.not-a-hash", runtime_info
    ), "A malformed build hash must be rejected")
