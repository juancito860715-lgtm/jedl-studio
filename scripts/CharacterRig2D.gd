extends RefCounted
class_name CharacterRig2D

const PART_NAMES := ["head", "torso", "arm_left", "arm_right", "leg_left", "leg_right"]


static func create_character(character_name: String, proportions: Dictionary = {}) -> Node2D:
	var root := Node2D.new()
	root.name = character_name.validate_node_name()
	root.set_meta("jedl_character_2d", true)
	root.set_meta("jedl_character_schema", 1)
	var specs: Array[Dictionary] = [
		{"name":"leg_left","position":Vector2(-13,42),"z":-2,"color":Color("#304B78"),"points":PackedVector2Array([Vector2(-9,-2),Vector2(8,-2),Vector2(10,38),Vector2(-8,38)])},
		{"name":"leg_right","position":Vector2(13,42),"z":-2,"color":Color("#304B78"),"points":PackedVector2Array([Vector2(-8,-2),Vector2(9,-2),Vector2(8,38),Vector2(-10,38)])},
		{"name":"torso","position":Vector2(0,0),"z":0,"color":Color("#3E8B9C"),"points":PackedVector2Array([Vector2(-22,-26),Vector2(22,-26),Vector2(19,28),Vector2(-19,28)])},
		{"name":"arm_left","position":Vector2(-25,-15),"z":1,"color":Color("#8A573E"),"points":PackedVector2Array([Vector2(-7,-5),Vector2(7,-5),Vector2(8,34),Vector2(-7,34)])},
		{"name":"arm_right","position":Vector2(25,-15),"z":1,"color":Color("#8A573E"),"points":PackedVector2Array([Vector2(-7,-5),Vector2(7,-5),Vector2(7,34),Vector2(-8,34)])},
		{"name":"head","position":Vector2(0,-53),"z":2,"color":Color("#8A573E"),"points":PackedVector2Array([Vector2(-22,-23),Vector2(-13,-31),Vector2(13,-31),Vector2(22,-23),Vector2(21,13),Vector2(12,28),Vector2(-12,28),Vector2(-21,13)])},
		{"name":"hair","position":Vector2.ZERO,"z":3,"color":Color("#332211"),"points":PackedVector2Array([Vector2(-22,-18),Vector2(-18,-31),Vector2(0,-36),Vector2(18,-31),Vector2(22,-18),Vector2(12,-23),Vector2(-12,-23)])}
	]
	for spec in specs:
		var part_name := String(spec["name"])
		var part := _make_part(part_name, spec["position"], spec["points"], spec["color"], int(spec["z"]))
		var part_scale: Variant = proportions.get(part_name, Vector2.ONE)
		if part_scale is Vector2:
			part.scale = part_scale
		if part_name == "hair":
			(root.get_node("head") as Node2D).add_child(part)
		else:
			root.add_child(part)
	var accessory := _make_part("accessory", Vector2(0,-30), PackedVector2Array([Vector2(-25,0),Vector2(25,0),Vector2(20,9),Vector2(-20,9)]), Color("#D9B45B"), 4)
	accessory.visible = false
	(root.get_node("head") as Node2D).add_child(accessory)
	return root


static func apply_appearance(character: Node2D, appearance: Dictionary) -> bool:
	if character == null or appearance.is_empty():
		return false
	var hair_color := Color.from_string(String(appearance.get("hair_color", "#332211")), Color("#332211"))
	var shirt_color := Color.from_string(String(appearance.get("shirt_color", "#3E8B9C")), Color("#3E8B9C"))
	var hair := character.get_node_or_null("head/hair/Shape") as Polygon2D
	if hair != null:
		hair.color = hair_color
	for part_name in ["torso", "arm_left", "arm_right"]:
		var shape := character.get_node_or_null(NodePath(part_name + "/Shape")) as Polygon2D
		if shape != null:
			shape.color = shirt_color
	var accessory_id := String(appearance.get("accessory", ""))
	var accessory := character.get_node_or_null("head/accessory") as Node2D
	if accessory != null:
		accessory.visible = not accessory_id.is_empty()
		var accessory_shape := accessory.get_node_or_null("Shape") as Polygon2D
		if accessory_shape != null:
			accessory_shape.color = shirt_color.darkened(0.18)
	character.set_meta("jedl_appearance", appearance.duplicate(true))
	return true


static func apply_pose(character: Node2D, pose: Dictionary) -> bool:
	if character == null:
		return false
	for part_name in PART_NAMES:
		var part := character.get_node_or_null(part_name) as Node2D
		if part == null:
			return false
		part.rotation_degrees = float(pose.get(part_name, 0.0))
	return true


static func register_pose_targets(engine: Node, target_prefix: String, character: Node2D) -> bool:
	if engine == null or character == null or target_prefix.strip_edges().is_empty() or not engine.has_method("register_target"):
		return false
	for part_name in PART_NAMES:
		var part := character.get_node_or_null(String(part_name)) as Node2D
		if part == null:
			return false
		var target_id: String = target_prefix + "." + String(part_name)
		if not bool(engine.call("register_target", target_id, part)):
			return false
	return true


static func add_pose_keyframes(engine: Node, target_prefix: String, character: Node2D, time_seconds: float, pose: Dictionary) -> bool:
	if engine == null or character == null or not engine.has_method("add_keyframe"):
		return false
	if not register_pose_targets(engine, target_prefix, character):
		return false
	for part_name in PART_NAMES:
		var target_id: String = target_prefix + "." + String(part_name)
		var rotation_value := Vector3(0.0, 0.0, float(pose.get(part_name, 0.0)))
		if not bool(engine.call("add_keyframe", target_id, "rotation_degrees", time_seconds, rotation_value)):
			return false
	return true


static func _make_part(part_name: String, part_position: Vector2, points: PackedVector2Array, color_value: Color, z_value: int) -> Node2D:
	var part := Node2D.new()
	part.name = part_name
	part.position = part_position
	part.z_index = z_value
	var pivot := Marker2D.new()
	pivot.name = "Pivot"
	pivot.position = Vector2.ZERO
	part.add_child(pivot)
	var shape := Polygon2D.new()
	shape.name = "Shape"
	shape.polygon = points
	shape.color = color_value
	part.add_child(shape)
	return part
