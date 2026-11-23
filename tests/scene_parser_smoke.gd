extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")


func _initialize() -> void:
	call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
	var world := Node3D.new()
	var canvas := Node2D.new()
	var manager = CatalogManagerScript.new()
	root.add_child(manager)
	assert(manager.load_catalog(), "Checked-in local asset manifest must load")
	root.add_child(world)
	root.add_child(canvas)
	var camera := Camera3D.new()
	camera.current = true
	root.add_child(camera)
	var subtitles := RichTextLabel.new()
	root.add_child(subtitles)
	var audio := AudioStreamPlayer.new()
	root.add_child(audio)
	var parser = SceneParserScript.new()
	root.add_child(parser)
	parser.world_root = world
	parser.canvas_root = canvas
	parser.camera = camera
	parser.subtitle_label = subtitles
	parser.catalog_manager = manager
	parser.audio_player = audio
	assert(parser.load_scene_file("res://scenes/scene.example.json"), "Example JSON should load offline")
	assert(parser.scene_data.has("characters"), "Scene should expose characters")
	assert(parser.active_instances.size() == 3, "Local 3D character and 2D cutouts should instantiate")
	assert(parser.timeline_engine.get_keyframe_count() == 5, "JSON actions should compile into deduplicated shared keyframes")
	assert(parser._events.size() == 4, "Subtitle timeline should contain display and clear events")
	parser.play_scene()
	assert(parser.timeline_engine.is_playing, "Timeline playback should start")
	print("GODOT_SMOKE_OK characters=1 transparent_2d=2 keyframes=5")
	quit(0)
