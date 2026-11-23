extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var world := Node3D.new()
	root.add_child(world)
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
	parser.catalog_manager = manager
	parser.camera = camera
	parser.subtitle_label = subtitle
	parser.audio_player = audio

	assert(parser.load_scene_file("res://scenes/scene.example.json"), "Example JSON must load")
	assert(parser.active_instances.size() == 3, "Example must instantiate the character and two transparent 2D elements")
	assert(parser.timeline_engine.get_keyframe_count() == 6, "JSON actions must be represented as editable keyframes")
	parser.seek_scene(1.0)
	var actor: Node3D
	for instance in parser.active_instances:
		if String(instance.get_meta("jedl_entry_id", "")) == "starter_actor":
			actor = instance
	assert(actor != null, "Stable scene entry ID must be attached to the instance")
	assert(actor.position.is_equal_approx(Vector3(0.4, 0.0, 0.0)), "JSON action must interpolate the actor at one second")
	assert(parser._events.size() == 4, "Two subtitles must create four timeline events")
	assert(parser._events[0]["kind"] == "subtitle", "Subtitle events must be sorted by time")

	parser.play_scene()
	assert(parser._playing, "Subtitle/audio event playback should start")
	parser._process(0.25)
	assert(subtitle.text == "JEDL Studio: escena local desde JSON", "First subtitle must appear at 0.25 seconds")
	parser.pause_scene()
	assert(parser.timeline_engine.is_paused, "Timeline pause must pause the shared animation engine")
	parser.resume_scene()
	assert(parser.timeline_engine.is_playing, "Timeline resume must resume the shared animation engine")
	parser.stop_scene()
	assert(not parser.timeline_engine.is_playing, "Stop must stop the shared timeline")

	var missing_scene := {
		"version": 2,
		"characters": [{"id": "missing_actor", "assetId": "character.does.not.exist.v1", "category": "Personajes 3D"}],
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
	camera.queue_free()
	subtitle.queue_free()
	audio.queue_free()
	manager.queue_free()
	print("SCENE_PARSER_TEST_OK")
	quit(0)
