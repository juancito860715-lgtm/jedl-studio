extends SceneTree

const MainScene = preload("res://Main.tscn")
const ProjectStoreScript = preload("res://scripts/ProjectStore.gd")


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
	assert(main.scene_parser.timeline_engine.get_keyframe_count() == 5, "Example JSON must use the shared timeline")
	var canvas_sprite_count := 0
	var stage_model_count := 0
	for scene_instance in main.scene_parser.active_instances:
		if scene_instance is Sprite2D:
			canvas_sprite_count += 1
			assert(scene_instance.get_parent() == main.canvas_2d_root, "2D resources must render in the independent 2D canvas, not the 3D world")
		elif scene_instance is Node3D:
			stage_model_count += 1
			assert(scene_instance.get_parent() == main.world_root, "3D resources must remain in the 3D stage")
	assert(canvas_sprite_count == 2 and stage_model_count == 1, "The example must separate 2D sprites from its 3D character")
	var leaf_sprite: Sprite2D
	for scene_instance in main.scene_parser.active_instances:
		if scene_instance is Sprite2D:
			leaf_sprite = scene_instance as Sprite2D
			break
	assert(leaf_sprite != null, "A 2D sprite must be available for transform editing")
	assert(main.scene_parser.timeline_engine.add_keyframe("leaf_demo", "position", 0.0, Vector3(1.0, 0.5, 0.0)), "2D canvas target must accept a shared-engine position keyframe")
	assert(main.scene_parser.timeline_engine.add_keyframe("leaf_demo", "rotation_degrees", 0.0, Vector3(0.0, 0.0, 30.0)), "2D canvas target must accept a rotation keyframe")
	assert(main.scene_parser.timeline_engine.add_keyframe("leaf_demo", "scale", 0.0, Vector3(0.5, 0.75, 1.0)), "2D canvas target must accept a scale keyframe")
	main.scene_parser.timeline_engine.seek(0.0)
	assert(leaf_sprite.position.is_equal_approx(Vector2(100.0, -50.0)), "Shared timeline transforms must map 2D world units to canvas pixels")
	assert(is_equal_approx(leaf_sprite.rotation_degrees, 30.0), "Shared timeline rotation must map to the 2D canvas rotation")
	assert(leaf_sprite.scale.is_equal_approx(Vector2(0.5, 0.75)), "Shared timeline scale must preserve 2D sprite scale")
	var gallery_asset: Dictionary = main.catalog_manager.scan_catalog("2d")[0]
	main._add_gallery_asset(String(gallery_asset["path"]), false, String(gallery_asset["id"]))
	assert(main.scene_parser.active_instances.size() == 4, "Adding a gallery item must create a separate scene instance")
	var inserted_sprite = main.scene_parser.active_instances.back()
	assert(inserted_sprite is Sprite2D and inserted_sprite.get_parent() == main.canvas_2d_root, "Inserted gallery PNG must enter the independent 2D canvas")
	assert(main.scene_parser.scene_data["elements"].size() == 3, "Inserted 2D resource identity and transform must be recorded in the project scene")
	main._save_project()
	var saved_timeline: Dictionary = main.scene_parser.timeline_engine.to_dictionary()
	assert(not saved_timeline.is_empty(), "Edited animation must be serialized with the project")
	assert(main.scene_parser.timeline_engine.delete_keyframe("leaf_demo", "position", 0.0), "Test mutation must change the in-memory animation")
	main._open_saved_project()
	assert(main.scene_parser.active_instances.size() == 4, "Opening a saved project must restore both 2D and 3D scene resources")
	assert(main.scene_parser.timeline_engine.to_dictionary() == saved_timeline, "Project reopen must restore the edited timeline exactly")
	var restored_leaf: Sprite2D
	for scene_instance in main.scene_parser.active_instances:
		if String(scene_instance.get_meta("jedl_entry_id", "")) == "leaf_demo":
			restored_leaf = scene_instance as Sprite2D
	assert(restored_leaf != null, "Reopened project must restore the original 2D resource identity")
	main.scene_parser.timeline_engine.seek(0.0)
	assert(restored_leaf.position.is_equal_approx(Vector2(100.0, -50.0)), "Reopened project must reproduce the saved 2D position")
	assert(is_equal_approx(restored_leaf.rotation_degrees, 30.0), "Reopened project must reproduce the saved 2D rotation")
	assert(restored_leaf.scale.is_equal_approx(Vector2(0.5, 0.75)), "Reopened project must reproduce the saved 2D scale")
	assert(main.timeline_tracks_list.get_child_count() == 5, "Timeline editor must display all five animated target/property tracks after project restoration")
	assert(main.timeline_tracks_list.get_child(0).get_child_count() == 4, "Position track must expose its three selectable keyframe markers")
	main.scene_parser.timeline_engine.seek(1.25)
	assert(is_equal_approx(main.timeline_slider.value, 1.25), "Timeline slider must follow playback-engine playhead changes")
	assert(is_equal_approx(main.timeline_time_spin.value, 1.25), "Timeline time field must follow playback-engine playhead changes")

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
	assert(main.scene_parser.active_instances.size() == 4, "Cancel must restore the previously loaded scene and inserted 2D resource")

	main.json_editor.text = JSON.stringify(missing_document)
	main._validate_and_load_json()
	main._choose_missing_alternative()
	assert(main.gallery_panel.visible, "Alternative choice must open the matching gallery")
	var alternative: Dictionary = main.catalog_manager.resolve_asset_id("character.jedl.starter.v1")
	main._add_gallery_asset(String(alternative["path"]), false, "character.jedl.starter.v1")
	assert(main.scene_parser.active_instances.size() == 1, "Choosing an alternative must reload the scene with that resource")
	var repaired: Dictionary = JSON.parse_string(main.json_editor.text)
	assert(repaired["characters"][0]["assetId"] == "character.jedl.starter.v1", "Alternative choice must replace the missing assetId explicitly")

	main.json_editor.text = JSON.stringify(main._blank_scene_document())
	main._show_json_editor()
	assert(main.json_panel.visible, "JSON editor must open")
	assert(JSON.parse_string(main.json_editor.text)["characters"].is_empty(), "New project JSON editor must begin with a blank scene")
	main._validate_and_load_json()
	assert(main.scene_parser.active_instances.is_empty(), "Blank JSON must replace the example with an empty composition")
	main._play_scene()
	assert(main.scene_parser.active_instances.is_empty(), "Play must not silently load a demo into a blank project")
	main.queue_free()
	for project_path in ["user://projects/current.json", "user://projects/current.backup.json", "user://projects/current.json.old", "user://projects/current.json.tmp"]:
		if FileAccess.file_exists(project_path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(project_path))
	print("CAMERA_FRAMING_TEST_OK")
	quit(0)
