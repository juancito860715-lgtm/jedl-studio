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

    # Integration: the app starts with a renderable sample scene and controls expose real content.
    await process_frame
    await process_frame
    assert(main.scene_parser != null, "Main UI must initialize the scene parser")
    assert(main.scene_parser.active_instances.size() == 1, "The sample Fox must be loaded when the app opens")
    assert(main.scene_parser.background_sprite != null, "The sample background must be loaded at startup")
    main._show_gallery("2d")
    assert(main.gallery_panel.visible, "The 2D gallery button must open a visible gallery panel")
    assert(main.gallery_list.get_child_count() == 4, "The 2D gallery must display all four packaged backgrounds")
    main._show_gallery("3d")
    assert(main.gallery_panel.visible, "The 3D gallery button must open a visible gallery panel")
    assert(main.gallery_list.get_child_count() == 7, "The 3D gallery must display six props and the Fox")
    main._show_json_editor()
    assert(main.json_panel.visible, "The JSON editor button must open the editor")
    main._validate_and_load_json()
    assert(not main.json_panel.visible, "A valid JSON scene must close the editor and reveal the composition")
    assert(main.scene_parser.active_instances.size() == 1, "JSON validation must instantiate the sample character")
    main._play_scene()
    assert(not main.json_panel.visible and not main.gallery_panel.visible,
        "Playback must never remain hidden behind an editor or gallery overlay")
    assert(main.scene_parser._playing, "Playback control must start the parsed scene")
    main.queue_free()
    print("CAMERA_FRAMING_TEST_OK")
    quit(0)
