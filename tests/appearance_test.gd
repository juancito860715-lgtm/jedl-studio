extends SceneTree

const RigScript = preload("res://scripts/CharacterRig2D.gd")
const StoreScript = preload("res://scripts/ProjectStore.gd")

func _initialize() -> void:
	var first = RigScript.create_character("first")
	var second = RigScript.create_character("second", {"head":Vector2(1.4,1.4),"torso":Vector2(0.8,1.2)})
	for part_name in ["head","torso","arm_left","arm_right","leg_left","leg_right"]:
		var part := first.get_node_or_null(part_name) as Node2D
		assert(part != null, "required part must exist: " + part_name)
		assert(part.get_node_or_null("Pivot") is Marker2D, "each part must expose its pivot")
	var first_torso := first.get_node("torso") as Node2D
	var before_position := first_torso.position
	var before_scale := first_torso.scale
	var appearance := {"name":"Urban","hair_color":"#332211","shirt_color":"#CC3344","accessory":"cap"}
	assert(RigScript.apply_appearance(first, appearance), "appearance should apply")
	assert(first_torso.position == before_position and first_torso.scale == before_scale, "appearance must not alter proportions")
	assert(RigScript.apply_appearance(second, appearance), "same appearance should apply to second character")
	assert((second.get_node("torso") as Node2D).scale != first_torso.scale, "appearance must preserve each character's proportions")
	var scene := {"characters":[],"objects":[],"elements":[],"subtitles":[],"sounds":[],"appearances":[appearance]}
	assert(StoreScript.save_project("hito2_appearance_roundtrip","Appearance test",scene,{}), "appearance project save must succeed")
	var loaded: Dictionary = StoreScript.load_project("hito2_appearance_roundtrip")
	assert(not loaded.is_empty(), "appearance project must reopen")
	var normalized = JSON.parse_string(JSON.stringify(loaded.get("scene",{})))
	assert(normalized.get("appearances",[]) == [appearance], "appearance must round-trip exactly")
	print("APPEARANCE_TEST_OK")
	quit(0)
