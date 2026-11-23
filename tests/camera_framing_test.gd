extends SceneTree

const MainScene = preload("res://Main.tscn")


func _initialize() -> void:
    call_deferred("_run_test")


func _run_test() -> void:
    var main := MainScene.instantiate()
    root.add_child(main)
    var distance: float = main._calculate_camera_distance(Vector3(2.0, 4.0, 1.0), 16.0 / 9.0, 55.0)
    assert(distance > 4.0, "Camera distance must fit a character taller than four units")
    var wide_distance: float = main._calculate_camera_distance(Vector3(8.0, 2.0, 1.0), 16.0 / 9.0, 55.0)
    assert(wide_distance > distance, "Wide characters must be framed using horizontal extent")
    var portrait_distance: float = main._calculate_camera_distance(Vector3(8.0, 2.0, 1.0), 9.0 / 16.0, 55.0)
    assert(portrait_distance > wide_distance, "Portrait viewports must fit a wide character using horizontal extent")

    # Integration: every project starts as a blank composition; demo content is opt-in.
    await process_frame
    await process_frame
    assert(main.scene_parser != null, "Main UI must initialize the scene parser")
    main._new_blank_scene()
    assert(main.scene_parser.active_instances.is_empty(), "A new composition must start with no preloaded character")
    assert(not main.scene_parser.scene_data.has("background"), "A new composition must not contain a photographic background")
    main._show_gallery("2d")
    assert(main.gallery_panel.visible, "The 2D gallery button must open a visible gallery panel")
    assert(main.gallery_list.get_child_count() == 1, "The empty 2D gallery must show its own empty-state message, not 3D resources")
    main._show_gallery("3d")
    assert(main.gallery_panel.visible, "The 3D gallery button must open a visible gallery panel")
    var gallery_3d_entries: Array[Dictionary] = main.catalog_manager.scan_catalog("3d")
    var expected_core_3d_ids := [
        "model.tree_stump_01",
        "model.tree_stump_02",
        "model.dead_quiver_branch_01",
        "model.dead_quiver_branch_02",
        "model.dead_quiver_trunk",
        "model.dead_tree_trunk_02",
        "model.ArmChair_01",
        "model.Barrel_02",
        "model.treasure_chest",
        "model.tool_cart",
        "model.trashbag",
        "character.fox.khronos.v1",
    ]
    var gallery_ids: Array[String] = []
    for entry in gallery_3d_entries:
        gallery_ids.append(String(entry.get("id", "")))
    for expected_id in expected_core_3d_ids:
        assert(gallery_ids.has(expected_id), "The 3D gallery is missing required core asset: " + expected_id)
    assert(gallery_3d_entries.size() >= expected_core_3d_ids.size(),
        "The 3D gallery must retain all eleven curated models and the animated Fox")
    assert(main.gallery_list.get_child_count() == gallery_3d_entries.size(),
        "The 3D gallery must render every catalog entry, including newly verified sources")
    main._show_json_editor()
    assert(main.json_panel.visible, "The JSON editor button must open the editor")
    main._validate_and_load_json()
    assert(not main.json_panel.visible, "A valid JSON scene must close the editor and reveal the composition")
    assert(main.scene_parser.active_instances.is_empty(), "Blank JSON must preserve an empty composition")
    var example_file := FileAccess.open("res://scenes/scene.example.json", FileAccess.READ)
    assert(example_file != null, "The optional Fox JSON example must be available")
    var example_json := example_file.get_as_text()
    example_file.close()
    assert(main.scene_parser.load_scene_text(example_json), "The optional Fox JSON example must load")
    assert(main.scene_parser.active_instances.size() == 1, "The optional Fox JSON example must instantiate its character")
    main._play_scene()
    assert(not main.json_panel.visible and not main.gallery_panel.visible,
        "Playback must never remain hidden behind an editor or gallery overlay")
    assert(main.scene_parser._playing, "Playback control must start the parsed scene")
    main.queue_free()
    print("CAMERA_FRAMING_TEST_OK")
    quit(0)
