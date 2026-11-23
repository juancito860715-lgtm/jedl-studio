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

	await process_frame
	await process_frame
	assert(main.scene_parser != null, "Main UI must initialize the scene parser")
	assert(main.scene_parser.active_instances.is_empty(), "A new project must start with an empty scene")
	assert(main.scene_parser.scene_data.has("characters"), "Blank project must have a valid scene document")
	main._show_gallery("2d")
	assert(main.gallery_panel.visible, "2D gallery must open")
	assert(main.gallery_list.get_child_count() == 3, "2D gallery must show all three local transparent sprites")
	main._show_gallery("3d")
	assert(main.gallery_panel.visible, "3D gallery must open independently")
	assert(main.gallery_list.get_child_count() == 1, "3D gallery must show the local starter character")
	main._load_example_scene()
	assert(main.scene_parser.active_instances.size() == 3, "Example scene must load its local character and 2D sprites")
	assert(main.scene_parser.timeline_engine.get_keyframe_count() == 6, "Example JSON must use the shared timeline")

	var missing_document := {
		"version": 2,
		"characters": [{"id": "missing_actor", "assetId": "character.not.available", "category": "Personajes 3D"}],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
	main.json_editor.text = JSON.stringify(missing_document)
	main._validate_and_load_json()
	assert(main.missing_alternative_button.visible, "Missing resource must offer an explicit same-category alternative")
	main._cancel_missing_resource()
	assert(main.scene_parser.active_instances.size() == 3, "Cancel must restore the previously loaded scene")

	main.json_editor.text = JSON.stringify(missing_document)
	main._validate_and_load_json()
	main._choose_missing_alternative()
	assert(main.gallery_panel.visible, "Alternative choice must open the matching gallery")
	var alternative: Dictionary = main.catalog_manager.resolve_asset_id("character.jedl.starter.v1")
	main._add_gallery_asset(String(alternative["path"]), false, "character.jedl.starter.v1")
	assert(main.scene_parser.active_instances.size() == 1, "Choosing an alternative must reload the scene with that resource")
	var repaired: Dictionary = JSON.parse_string(main.json_editor.text)
	assert(repaired["characters"][0]["assetId"] == "character.jedl.starter.v1", "Alternative choice must replace the missing assetId explicitly")

	main._show_json_editor()
	assert(main.json_panel.visible, "JSON editor must open")
	assert(JSON.parse_string(main.json_editor.text)["characters"].is_empty(), "New project JSON editor must begin with a blank scene")
	main._validate_and_load_json()
	assert(main.scene_parser.active_instances.is_empty(), "Blank JSON must replace the example with an empty composition")
	main._play_scene()
	assert(main.scene_parser.active_instances.is_empty(), "Play must not silently load a demo into a blank project")
	main.queue_free()
	print("CAMERA_FRAMING_TEST_OK")
	quit(0)
