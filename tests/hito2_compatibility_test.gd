extends SceneTree

const ParserScript = preload("res://scripts/SceneParser.gd")

func _initialize() -> void:
	var parser = ParserScript.new()
	root.add_child(parser)
	var world := Node3D.new()
	var canvas := Node2D.new()
	var camera := Camera3D.new()
	root.add_child(world)
	root.add_child(canvas)
	root.add_child(camera)
	parser.world_root = world
	parser.canvas_root = canvas
	parser.camera = camera
	var old_document := {"version":2,"characters":[],"objects":[],"elements":[],"subtitles":[],"sounds":[],"actions":[]}
	assert(parser.load_scene_text(JSON.stringify(old_document)), "pre-Hito-2 project without appearances/style must load")
	assert(not parser.scene_data.has("appearances") and not parser.scene_data.has("style"), "legacy scene fields must remain optional")
	print("HITO2_COMPATIBILITY_TEST_OK")
	quit(0)
