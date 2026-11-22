extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")
const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var manager = CatalogManagerScript.new()
    root.add_child(manager)

    var entries_2d: Array[Dictionary] = manager.scan_catalog("2d")
    assert(entries_2d.size() == 4, "The 2D gallery must contain the four curated photographic forest/river backgrounds")
    for item in entries_2d:
        assert(String(item["path"]).ends_with(".jpg"), "The public 2D gallery must not expose rudimentary generated PNG parts")
        assert(item["license"] == "CC0-1.0", "Every 2D image must have verified redistribution rights")
        assert(item["offline"] and item["placeable"], "Every 2D background must be packaged and placeable")
        assert(ResourceLoader.exists(String(item["preview_path"])), "Every 2D card must have a packaged preview")

    var models: Array[Dictionary] = manager.scan_catalog("3d")
    assert(models.size() == 7, "The 3D gallery must expose six realistic environment models plus the animated Fox")
    assert(models.any(func(item: Dictionary) -> bool: return item["id"] == "character.fox.khronos.v1"), "The animated Fox test character must remain in the gallery")
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
    parser.camera = camera
    assert(parser.add_catalog_asset(String(entries_2d[0]["path"])),
        "The scene engine must place a selected photographic 2D background")
    assert(parser.background_sprite != null and parser.background_sprite.get_parent() == camera,
        "A selected 2D background must be a camera-following far-plane sprite behind all 3D objects")
    assert(parser.active_instances.is_empty(),
        "A 2D backplate must not distort 3D scene framing or be counted as a 3D object")
    assert(parser.add_catalog_asset(String(models[0]["path"])),
        "The scene engine must place a selected realistic 3D model")
    assert(parser.active_instances.size() == 1 and parser.active_instances.back() is Node3D,
        "A selected 3D model must become a Node3D scene instance")
    var cutout_image := Image.create(16, 16, false, Image.FORMAT_RGBA8)
    cutout_image.fill(Color(1.0, 1.0, 1.0, 0.5))
    var cutout_texture := ImageTexture.create_from_image(cutout_image)
    var cutout := parser._create_2d_element(cutout_texture)
    assert(cutout.texture == cutout_texture, "Individual 2D cutouts must retain their texture")
    assert(cutout.billboard == BaseMaterial3D.BILLBOARD_ENABLED, "Individual 2D cutouts must face the scene camera")
    assert(cutout.material_override.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA,
        "Individual 2D cutouts must preserve transparent edges")
    cutout.free()

    parser.queue_free()
    camera.queue_free()
    world.queue_free()
    manager.queue_free()
    print("CATALOG_MANAGER_TEST_OK")
    quit(0)
