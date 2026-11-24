extends SceneTree

func _initialize() -> void:
	var gesture_script = load("res://scripts/TouchGestureController.gd")
	if not _check(gesture_script != null, "TouchGestureController.gd must load"):
		return
	var target := Node2D.new()
	var controller = gesture_script.new()
	var first := InputEventScreenTouch.new()
	first.index = 0
	first.position = Vector2(10,10)
	first.pressed = true
	if not _check(controller.handle_event(first, target), "first touch must be accepted"):
		return
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(20,15)
	drag.relative = Vector2(10,5)
	controller.handle_event(drag, target)
	if not _check(target.position.is_equal_approx(Vector2(10,5)), "single finger drag must move selected target"):
		return
	var second := InputEventScreenTouch.new()
	second.index = 1
	second.position = Vector2(40,15)
	second.pressed = true
	controller.handle_event(second, target)
	var pinch := InputEventScreenDrag.new()
	pinch.index = 1
	pinch.position = Vector2(50,15)
	pinch.relative = Vector2(10,0)
	controller.handle_event(pinch, target)
	if not _check(is_equal_approx(target.scale.x, 1.5), "two finger spread must scale target"):
		return
	var rotate := InputEventScreenDrag.new()
	rotate.index = 1
	rotate.position = Vector2(40,25)
	rotate.relative = Vector2(-10,10)
	controller.handle_event(rotate, target)
	if not _check(absf(target.rotation_degrees - 26.565) < 0.1, "two finger turn must rotate target"):
		return
	if not _check(target.scale.x >= 0.2 and target.scale.x <= 5.0, "scale must stay within safe limits"):
		return
	var scene_entry: Dictionary = {}
	controller.sync_scene_entry(scene_entry, target)
	if not _check(scene_entry.has("position") and scene_entry.has("scale") and scene_entry.has("rotation_degrees"), "gesture transforms must persist to scene data"):
		return
	var scaled_target := Node2D.new()
	var scaled_controller = gesture_script.new()
	scaled_controller.coordinate_transform = Transform2D(Vector2(0.5,0), Vector2(0,0.5), Vector2.ZERO)
	var scaled_touch := InputEventScreenTouch.new()
	scaled_touch.index = 0
	scaled_touch.position = Vector2(10,10)
	scaled_touch.pressed = true
	scaled_controller.handle_event(scaled_touch, scaled_target)
	var scaled_drag := InputEventScreenDrag.new()
	scaled_drag.index = 0
	scaled_drag.position = Vector2(20,15)
	scaled_controller.handle_event(scaled_drag, scaled_target)
	if not _check(scaled_target.position.is_equal_approx(Vector2(5,2.5)), "gesture positions must convert from viewport to canvas-local coordinates"):
		return
	# Scale limits are part of the public touch-gesture contract.
	var upper_target := Node2D.new()
	var upper_controller = gesture_script.new()
	var upper_first := InputEventScreenTouch.new()
	upper_first.index = 0
	upper_first.position = Vector2.ZERO
	upper_first.pressed = true
	upper_controller.handle_event(upper_first, upper_target)
	var upper_second := InputEventScreenTouch.new()
	upper_second.index = 1
	upper_second.position = Vector2(1, 0)
	upper_second.pressed = true
	upper_controller.handle_event(upper_second, upper_target)
	var upper_drag := InputEventScreenDrag.new()
	upper_drag.index = 1
	upper_drag.position = Vector2(500, 0)
	upper_controller.handle_event(upper_drag, upper_target)
	if not _check(is_equal_approx(upper_target.scale.x, 5.0), "pinch above maximum must clamp scale.x to exactly 5.0"):
		return

	var lower_target := Node2D.new()
	var lower_controller = gesture_script.new()
	var lower_first := InputEventScreenTouch.new()
	lower_first.index = 0
	lower_first.position = Vector2.ZERO
	lower_first.pressed = true
	lower_controller.handle_event(lower_first, lower_target)
	var lower_second := InputEventScreenTouch.new()
	lower_second.index = 1
	lower_second.position = Vector2(40, 0)
	lower_second.pressed = true
	lower_controller.handle_event(lower_second, lower_target)
	var lower_drag := InputEventScreenDrag.new()
	lower_drag.index = 1
	lower_drag.position = Vector2(1, 0)
	lower_controller.handle_event(lower_drag, lower_target)
	if not _check(is_equal_approx(lower_target.scale.x, 0.2), "pinch below minimum must clamp scale.x to exactly 0.2"):
		return

	# Scene serialization contract: 100 canvas pixels per scene unit, with Y inverted.
	var persisted_target := Node2D.new()
	persisted_target.position = Vector2(200, -150)
	persisted_target.scale = Vector2(1.25, 0.75)
	persisted_target.rotation_degrees = 37.0
	var persisted_entry: Dictionary = {}
	controller.sync_scene_entry(persisted_entry, persisted_target)
	var saved_position: Array = persisted_entry["position"]
	var saved_scale: Array = persisted_entry["scale"]
	var saved_rotation: Array = persisted_entry["rotation_degrees"]
	if not _check(is_equal_approx(float(saved_position[0]), 2.0) and is_equal_approx(float(saved_position[1]), 1.5) and is_equal_approx(float(saved_position[2]), 0.0), "scene position contract must map (200,-150) px to [2.0,1.5,0.0]"):
		return
	if not _check(is_equal_approx(float(saved_scale[0]), 1.25) and is_equal_approx(float(saved_scale[1]), 0.75) and is_equal_approx(float(saved_scale[2]), 1.0), "scene scale contract must persist X/Y and neutral Z"):
		return
	if not _check(is_equal_approx(float(saved_rotation[0]), 0.0) and is_equal_approx(float(saved_rotation[1]), 0.0) and is_equal_approx(float(saved_rotation[2]), 37.0), "scene rotation contract must persist degrees in Z"):
		return
	var parser_script = load("res://scripts/SceneParser.gd")
	if not _check(parser_script != null, "SceneParser must load for the inverse transform contract"):
		return
	var parser = parser_script.new()
	var restored_target := Node2D.new()
	parser._apply_instance_transform(
		restored_target,
		Vector3(float(saved_position[0]), float(saved_position[1]), float(saved_position[2])),
		Vector3(float(saved_rotation[0]), float(saved_rotation[1]), float(saved_rotation[2])),
		Vector3(float(saved_scale[0]), float(saved_scale[1]), float(saved_scale[2]))
	)
	if not _check(restored_target.position.is_equal_approx(persisted_target.position), "scene position must round-trip to the same visible canvas position"):
		return
	if not _check(restored_target.scale.is_equal_approx(persisted_target.scale), "scene scale must round-trip"):
		return
	if not _check(is_equal_approx(restored_target.rotation_degrees, persisted_target.rotation_degrees), "scene rotation must round-trip"):
		return

	# Releasing one pinch finger must preserve the remaining finger's drag origin.
	var transition_target := Node2D.new()
	var transition_controller = gesture_script.new()
	var transition_first := InputEventScreenTouch.new()
	transition_first.index = 0
	transition_first.position = Vector2.ZERO
	transition_first.pressed = true
	transition_controller.handle_event(transition_first, transition_target)
	var transition_second := InputEventScreenTouch.new()
	transition_second.index = 1
	transition_second.position = Vector2(40, 0)
	transition_second.pressed = true
	transition_controller.handle_event(transition_second, transition_target)
	var transition_pinch := InputEventScreenDrag.new()
	transition_pinch.index = 1
	transition_pinch.position = Vector2(60, 0)
	transition_controller.handle_event(transition_pinch, transition_target)
	var scale_after_pinch := transition_target.scale
	var position_before_release := transition_target.position
	var release_second := InputEventScreenTouch.new()
	release_second.index = 1
	release_second.position = Vector2(60, 0)
	release_second.pressed = false
	transition_controller.handle_event(release_second, transition_target)
	if not _check(transition_target.position.is_equal_approx(position_before_release), "releasing a pinch finger must not move the target"):
		return
	var remaining_drag := InputEventScreenDrag.new()
	remaining_drag.index = 0
	remaining_drag.position = Vector2(30, 0)
	remaining_drag.relative = Vector2(30, 0)
	transition_controller.handle_event(remaining_drag, transition_target)
	if not _check(transition_target.position.is_equal_approx(position_before_release + Vector2(30, 0)), "remaining finger must drag 30 px from its last known position without a jump"):
		return
	var scale_before_stale_drag := transition_target.scale
	var stale_drag := InputEventScreenDrag.new()
	stale_drag.index = 1
	stale_drag.position = Vector2(90, 0)
	stale_drag.relative = Vector2(30, 0)
	if not _check(not transition_controller.handle_event(stale_drag, transition_target), "a drag from the lifted finger must be ignored"):
		return
	if not _check(transition_target.scale.is_equal_approx(scale_before_stale_drag) and scale_after_pinch.is_equal_approx(scale_before_stale_drag), "scale must not change while only one finger remains"):
		return
	var release_first := InputEventScreenTouch.new()
	release_first.index = 0
	release_first.position = Vector2(30, 0)
	release_first.pressed = false
	transition_controller.handle_event(release_first, transition_target)
	var new_touch := InputEventScreenTouch.new()
	new_touch.index = 0
	new_touch.position = Vector2(100, 100)
	new_touch.pressed = true
	transition_controller.handle_event(new_touch, transition_target)
	var new_drag := InputEventScreenDrag.new()
	new_drag.index = 0
	new_drag.position = Vector2(110, 100)
	new_drag.relative = Vector2(10, 0)
	transition_controller.handle_event(new_drag, transition_target)
	if not _check(transition_target.position.is_equal_approx(position_before_release + Vector2(40, 0)), "a fresh one-finger gesture must work after both fingers are released"):
		return

	print("TRANSFORM_GESTURE_TEST_OK")
	quit(0)


func _check(condition: bool, message: String) -> bool:
	if not condition:
		push_error("TRANSFORM_GESTURE_TEST_FAILED: " + message)
		quit(1)
		return false
	return true
