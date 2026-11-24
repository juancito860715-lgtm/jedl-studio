extends SceneTree

const StoreScript = preload("res://scripts/ProjectStore.gd")

func _initialize() -> void:
	var rig_script = load("res://scripts/CharacterRig2D.gd")
	if not _check(rig_script != null, "CharacterRig2D.gd must load"):
		return
	var first = rig_script.create_character("first")
	var second = rig_script.create_character("second", {"head":Vector2(1.4,1.4),"torso":Vector2(0.8,1.2)})
	for part_name in ["head","torso","arm_left","arm_right","leg_left","leg_right"]:
		var part := first.get_node_or_null(part_name) as Node2D
		if not _check(part != null, "required part must exist: " + part_name):
			return
		if not _check(part.get_node_or_null("Pivot") is Marker2D, "each part must expose its pivot"):
			return
	var first_torso := first.get_node("torso") as Node2D
	var before_position := first_torso.position
	var before_scale := first_torso.scale
	var appearance := {"name":"Urban","hair_color":"#332211","shirt_color":"#CC3344","accessory":"cap"}
	if not _check(rig_script.apply_appearance(first, appearance), "appearance should apply"):
		return
	var hair_shape := first.get_node("head/hair/Shape") as Polygon2D
	var shirt_shape := first.get_node("torso/Shape") as Polygon2D
	var arm_shape := first.get_node("arm_left/Shape") as Polygon2D
	if not _check(hair_shape.color == Color("#332211"), "hair color must change"):
		return
	if not _check(shirt_shape.color == Color("#CC3344") and arm_shape.color == Color("#CC3344"), "shirt color must apply to torso and arms"):
		return
	if not _check(first_torso.position == before_position and first_torso.scale == before_scale, "appearance must not alter proportions"):
		return
	if not _check(rig_script.apply_appearance(second, appearance), "same appearance should apply to second character"):
		return
	if not _check((second.get_node("torso") as Node2D).scale != first_torso.scale, "appearance must preserve each character's proportions"):
		return
	var scene := {"characters":[],"objects":[],"elements":[],"subtitles":[],"sounds":[],"appearances":[appearance]}
	if not _check(StoreScript.save_project("hito2_appearance_roundtrip","Appearance test",scene,{}), "appearance project save must succeed"):
		return
	var loaded: Dictionary = StoreScript.load_project("hito2_appearance_roundtrip")
	if not _check(not loaded.is_empty(), "appearance project must reopen"):
		return
	var normalized = JSON.parse_string(JSON.stringify(loaded.get("scene",{})))
	if not _check(normalized.get("appearances",[]) == [appearance], "appearance must round-trip exactly"):
		return
	print("APPEARANCE_TEST_OK")
	quit(0)


func _check(condition: bool, message: String) -> bool:
	if not condition:
		push_error("APPEARANCE_TEST_FAILED: " + message)
		quit(1)
		return false
	return true
