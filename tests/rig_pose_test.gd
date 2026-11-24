extends SceneTree

const TimelineScript = preload("res://scripts/TimelineEngine.gd")

func _initialize() -> void:
	var rig_script = load("res://scripts/CharacterRig2D.gd")
	if not _check(rig_script != null, "CharacterRig2D.gd must load"):
		return
	var character = rig_script.create_character("pose_actor")
	var first_pose := {"head":0.0,"arm_left":-30.0,"arm_right":30.0,"leg_left":10.0}
	if not _check(rig_script.apply_pose(character, first_pose), "pose must apply"):
		return
	if not _check(is_equal_approx((character.get_node("arm_left") as Node2D).rotation_degrees,-30.0), "left arm angle must apply"):
		return
	if not _check(is_zero_approx((character.get_node("torso") as Node2D).rotation_degrees), "unlisted parts must reset to zero"):
		return
	var engine = TimelineScript.new()
	var second_pose := {"head":20.0,"arm_left":30.0,"arm_right":-30.0,"leg_left":-10.0,"leg_right":10.0}
	if not _check(rig_script.add_pose_keyframes(engine,"pose_actor",character,0.0,first_pose), "first pose keyframes must use shared timeline"):
		return
	if not _check(rig_script.add_pose_keyframes(engine,"pose_actor",character,1.0,second_pose), "second pose keyframes must use shared timeline"):
		return
	engine.seek(0.5)
	if not _check(absf((character.get_node("arm_left") as Node2D).rotation_degrees) < 0.001, "pose midpoint must interpolate left arm"):
		return
	if not _check(absf((character.get_node("head") as Node2D).rotation_degrees - 10.0) < 0.001, "pose midpoint must interpolate head"):
		return
	var serialized: Dictionary = engine.to_dictionary()
	var restored_character = rig_script.create_character("restored_pose_actor")
	var restored_engine = TimelineScript.new()
	if not _check(rig_script.register_pose_targets(restored_engine,"pose_actor",restored_character), "pose targets must be re-registered after reopening"):
		return
	if not _check(restored_engine.load_dictionary(serialized), "existing timeline format must restore pose tracks"):
		return
	restored_engine.seek(0.5)
	if not _check(absf((restored_character.get_node("arm_left") as Node2D).rotation_degrees) < 0.001, "restored arm pose must interpolate"):
		return
	if not _check(absf((restored_character.get_node("head") as Node2D).rotation_degrees - 10.0) < 0.001, "restored head pose must interpolate"):
		return
	print("RIG_POSE_TEST_OK")
	quit(0)


func _check(condition: bool, message: String) -> bool:
	if not condition:
		push_error("RIG_POSE_TEST_FAILED: " + message)
		quit(1)
		return false
	return true
