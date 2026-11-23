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
	print("TRANSFORM_GESTURE_TEST_OK")
	quit(0)


func _check(condition: bool, message: String) -> bool:
	if not condition:
		push_error("TRANSFORM_GESTURE_TEST_FAILED: " + message)
		quit(1)
		return false
	return true
