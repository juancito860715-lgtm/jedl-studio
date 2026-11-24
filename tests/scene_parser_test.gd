extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var world := Node3D.new()
	var canvas := Node2D.new()
	root.add_child(world)
	root.add_child(canvas)
	var manager = CatalogManagerScript.new()
	root.add_child(manager)
	assert(manager.load_catalog(), "Local starter manifest must validate")
	var subtitle := Label.new()
	root.add_child(subtitle)
	var audio := AudioStreamPlayer.new()
	root.add_child(audio)
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.current = true
	var parser = SceneParserScript.new()
	root.add_child(parser)
	parser.world_root = world
	parser.canvas_root = canvas
	parser.catalog_manager = manager
	parser.camera = camera
	parser.subtitle_label = subtitle
	parser.audio_player = audio

	assert(parser.load_scene_file("res://scenes/scene.example.json"), "Example JSON must load")
	assert(parser.active_instances.size() == 3, "Example must instantiate one rigged 3D pedestrian and two transparent 2D auxiliary elements")
	assert(parser.timeline_engine.get_keyframe_count() == 4, "The pedestrian and auxiliary leaf must each compile two keyframes")
	var canvas_sprite_count := 0
	for scene_instance in parser.active_instances:
		if scene_instance is Sprite2D:
			canvas_sprite_count += 1
			assert(scene_instance.get_parent() == canvas, "Every 2D scene element must be parented to the dedicated canvas")
	assert(canvas_sprite_count == 2, "JSON 2D elements must instantiate as Sprite2D nodes")
	parser.seek_scene(1.0)
	assert(parser.active_instances.filter(func(item: Node): return item.has_meta("jedl_character_format")).size() == 1, "Example must instantiate exactly one certified 3D character")
	assert(parser._events.size() == 4, "Two subtitles must create four timeline events")
	assert(parser._events[0]["kind"] == "subtitle", "Subtitle events must be sorted by time")

	parser.play_scene()
	assert(parser._playing, "Subtitle/audio event playback should start")
	parser._process(0.25)
	assert(subtitle.text == "JEDL Studio: escena de elementos locales", "First subtitle must appear at 0.25 seconds")
	parser.pause_scene()
	assert(parser.timeline_engine.is_paused, "Timeline pause must pause the shared animation engine")
	parser.resume_scene()
	assert(parser.timeline_engine.is_playing, "Timeline resume must resume the shared animation engine")
	parser.stop_scene()
	assert(not parser.timeline_engine.is_playing, "Stop must stop the shared timeline")

	assert(parser.load_scene_file("res://scenes/escena_cruce_coche.json"), "Crossing-car scene must load with all pinned local assets")
	assert(parser.active_instances.size() == 9, "Crossing-car scene must instantiate one pedestrian, one car and seven modular environment instances")
	assert(parser.scene_data["characters"].size() == 1 and parser.scene_data["characters"][0]["assetId"] == "character.tevy.casual_walker.v1", "Crossing scene must bind the actual rigged pedestrian")
	assert(not parser.scene_data.has("characters_2d"), "Migrated scene must not contain the prohibited characters_2d field")
	assert(parser.scene_data["resource_requirements"].size() == 3, "Scene must declare real character, vehicle and modular environment requirements")
	assert(parser.scene_data["motion_plan"][0]["status"] == "asset_and_animation_bound", "Pedestrian walk animation must be bound to the installed 3D model")
	assert(parser.scene_data["scene_spec"]["story_beats"].size() == 3, "Crossing scene must define pedestrian, door and driving beats")
	assert(parser.scene_data["audio_sync"]["cues"].size() == 3, "Crossing scene must synchronize footsteps, door and engine cues")
	assert(parser.scene_data["sounds"].map(func(item: Dictionary): return String(item["id"])) == ["footsteps", "car_door", "car_engine"], "All three requested sound cues must be present in timeline order")
	for sound in parser.scene_data["sounds"]:
		assert(FileAccess.file_exists(String(sound["path"])), "Every scene sound must exist as a packaged local WAV")
	assert(parser.timeline_engine.get_tracks_snapshot().size() == 2, "JSON must compile pedestrian and vehicle movement tracks")

	var missing_scene := {
		"version": 2,
		"characters": [{"id": "missing_actor", "format": "3d", "assetId": "character.does.not.exist.v1", "category": "Personajes 3D"}],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
	assert(not parser.load_scene_text(JSON.stringify(missing_scene)), "Unknown asset IDs must fail explicitly")
	assert(parser.last_missing_entry_id == "missing_actor", "Missing resource must identify the JSON entry")
	assert(parser.last_missing_kind == "3d" and parser.last_missing_category == "Personajes 3D",
		"Missing resource must expose its category for explicit alternatives")
	assert(parser.last_error.contains("assetId"), "Missing resource must provide a clear error")

	parser.queue_free()
	world.queue_free()
	canvas.queue_free()
	camera.queue_free()
	subtitle.queue_free()
	audio.queue_free()
	manager.queue_free()
	print("SCENE_PARSER_TEST_OK")
	quit(0)
