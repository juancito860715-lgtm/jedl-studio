extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var parser = SceneParserScript.new()
	root.add_child(parser)

	var legacy_scene := {
		"version": 2,
		"characters": [],
		"characters_2d": [{"id": "legacy_capsule_actor"}],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
	assert(not parser.load_scene_text(JSON.stringify(legacy_scene)),
		"Legacy characters_2d must be rejected; geometric procedural characters are not product characters")
	assert(parser.last_error.contains("2.5d") or parser.last_error.contains("2D"),
		"Legacy rejection must explain the supported character formats")

	var missing_format_scene := {
		"version": 2,
		"characters": [{"id": "untyped_character", "assetId": "not.used"}],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
	assert(not parser.load_scene_text(JSON.stringify(missing_format_scene)),
		"Characters must declare format 2.5d or 3d")

	var unsupported_format_scene := {
		"version": 2,
		"characters": [{"id": "flat_actor", "format": "2d", "assetId": "not.used"}],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
	assert(not parser.load_scene_text(JSON.stringify(unsupported_format_scene)),
		"2D character format must be rejected")

	var invalid_root_2d := Node2D.new()
	assert(not SceneParserScript.is_character_rig_compatible(invalid_root_2d, "2.5d"),
		"2.5D characters must use a spatial rigged scene, not a flat procedural Node2D")
	var invalid_root_3d := Node3D.new()
	assert(not SceneParserScript.is_character_rig_compatible(invalid_root_3d, "3d"),
		"3D characters without a real Skeleton3D must be rejected")

	var rig_25d := Node3D.new()
	var skeleton_25d := Skeleton3D.new()
	skeleton_25d.add_bone("root")
	rig_25d.add_child(skeleton_25d)
	var attachment := BoneAttachment3D.new()
	attachment.bone_name = "root"
	skeleton_25d.add_child(attachment)
	var sprite := Sprite3D.new()
	var image := Image.create(2, 2, false, Image.FORMAT_RGBA8)
	sprite.texture = ImageTexture.create_from_image(image)
	attachment.add_child(sprite)
	assert(SceneParserScript.is_character_rig_compatible(rig_25d, "2.5d"),
		"2.5D characters must have a Skeleton3D and illustrated Sprite3D parts attached to bones")
	assert(not SceneParserScript.is_character_rig_compatible(rig_25d, "3d"),
		"2.5D cutout rigs must not be mislabeled as volumetric 3D characters")

	var rig_3d := Node3D.new()
	var skeleton_3d := Skeleton3D.new()
	skeleton_3d.add_bone("root")
	rig_3d.add_child(skeleton_3d)
	var mesh_instance := MeshInstance3D.new()
	mesh_instance.mesh = BoxMesh.new()
	mesh_instance.skin = Skin.new()
	mesh_instance.skeleton = NodePath("../Skeleton3D")
	rig_3d.add_child(mesh_instance)
	assert(SceneParserScript.is_character_rig_compatible(rig_3d, "3d"),
		"3D characters must contain a Skeleton3D and a skinned MeshInstance3D")
	assert(not SceneParserScript.is_character_rig_compatible(rig_3d, "2.5d"),
		"Volumetric 3D characters must not be mislabeled as 2.5D cutout rigs")

	parser.queue_free()
	rig_25d.queue_free()
	rig_3d.queue_free()
	invalid_root_2d.queue_free()
	invalid_root_3d.queue_free()
	print("CHARACTER_FORMAT_CONTRACT_TEST_OK")
	quit(0)
