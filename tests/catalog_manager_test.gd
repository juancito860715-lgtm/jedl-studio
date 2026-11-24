extends SceneTree

const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")
const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var manager = CatalogManagerScript.new()
	root.add_child(manager)
	assert(manager.load_catalog(), "Checked-in local catalog must validate against its manifest")
	var sprites: Array[Dictionary] = manager.scan_catalog("2d")
	assert(sprites.size() == 3, "Independent 2D gallery must expose the three local transparent sprites")
	for item in sprites:
		assert(String(item["path"]).ends_with(".png"), "2D starter assets must be PNG")
		assert(item["alpha"] == true, "Every 2D sprite must declare transparency")
		assert(item["license"] == "CC0-1.0", "Every starter sprite must have its verified license")
		assert(ResourceLoader.exists(String(item["path"])), "Every 2D sprite must be packaged locally")
	var models: Array[Dictionary] = manager.scan_catalog("3d")
	assert(models.is_empty(), "Unrigged geometric starter must not appear as a selectable 3D character")

	var world := Node3D.new()
	var canvas := Node2D.new()
	root.add_child(world)
	root.add_child(canvas)
	var camera := Camera3D.new()
	root.add_child(camera)
	var parser = SceneParserScript.new()
	root.add_child(parser)
	parser.world_root = world
	parser.canvas_root = canvas
	parser.camera = camera
	parser.catalog_manager = manager
	assert(parser.load_scene_file("res://scenes/scene.example.json"), "Example scene must load from checked-in assets")
	assert(parser.active_instances.size() == 2, "Sample must instantiate only two auxiliary 2D cutouts")
	assert(parser.timeline_engine.get_keyframe_count() == 2, "Sample scene must animate an auxiliary element only")
	assert(parser.timeline_engine.duration_seconds == 2.0, "Auxiliary element timeline duration must be two seconds")

	parser.queue_free()
	camera.queue_free()
	world.queue_free()
	canvas.queue_free()
	manager.queue_free()
	print("CATALOG_MANAGER_TEST_OK")
	quit(0)
