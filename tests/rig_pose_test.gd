extends SceneTree

const TimelineScript = preload("res://scripts/TimelineEngine.gd")

func _initialize() -> void:
	var rig_script = load("res://scripts/CharacterRig2D.gd")
	assert(rig_script != null, "CharacterRig2D.gd must be implemented after this red test")
	var character = rig_script.create_character("pose_actor")
	var first_pose := {"head":0.0,"arm_left":-30.0,"arm_right":30.0,"leg_left":10.0}
	assert(rig_script.apply_pose(character, first_pose), "pose must apply")
	assert(is_equal_approx((character.get_node("arm_left") as Node2D).rotation_degrees,-30.0), "left arm angle must apply")
	assert(is_zero_approx((character.get_node("torso") as Node2D).rotation_degrees), "unlisted parts must reset to zero")
	var engine = TimelineScript.new()
	var second_pose := {"head":20.0,"arm_left":30.0,"arm_right":-30.0,"leg_left":-10.0,"leg_right":10.0}
	assert(rig_script.add_pose_keyframes(engine,"pose_actor",character,0.0,first_pose), "first pose keyframes must use shared timeline")
	assert(rig_script.add_pose_keyframes(engine,"pose_actor",character,1.0,second_pose), "second pose keyframes must use shared timeline")
	engine.seek(0.5)
	assert(absf((character.get_node("arm_left") as Node2D).rotation_degrees) < 0.001, "pose midpoint must interpolate left arm")
	assert(absf((character.get_node("head") as Node2D).rotation_degrees - 10.0) < 0.001, "pose midpoint must interpolate head")
	print("RIG_POSE_TEST_OK")
	quit(0)
