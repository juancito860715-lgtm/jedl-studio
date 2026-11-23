extends SceneTree

func _initialize() -> void:
	var gesture_script = load("res://scripts/TouchGestureController.gd")
	assert(gesture_script != null, "TouchGestureController.gd must be implemented after this red test")
	var target := Node2D.new()
	var controller = gesture_script.new()
	var first := InputEventScreenTouch.new()
	first.index = 0
	first.position = Vector2(10,10)
	first.pressed = true
	controller.handle_event(first, target)
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(20,15)
	drag.relative = Vector2(10,5)
	controller.handle_event(drag, target)
	assert(target.position.is_equal_approx(Vector2(10,5)), "single finger drag must move selected target")
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
	assert(is_equal_approx(target.scale.x, 1.5), "two finger spread must scale target")
	var rotate := InputEventScreenDrag.new()
	rotate.index = 1
	rotate.position = Vector2(40,25)
	rotate.relative = Vector2(-10,10)
	controller.handle_event(rotate, target)
	assert(absf(target.rotation_degrees - 26.565) < 0.1, "two finger turn must rotate target")
	assert(target.scale.x >= 0.2 and target.scale.x <= 5.0, "scale must stay within safe limits")
	var scene_entry := {}
	controller.sync_scene_entry(scene_entry, target)
	assert(scene_entry.has("position") and scene_entry.has("scale") and scene_entry.has("rotation_degrees"), "gesture transforms must persist to scene data")
	print("TRANSFORM_GESTURE_TEST_OK")
	quit(0)
