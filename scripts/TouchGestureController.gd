extends RefCounted
class_name TouchGestureController

const MIN_SCALE := 0.2
const MAX_SCALE := 5.0

var _touch_positions: Dictionary = {}
var _initial_distance := 0.0
var _initial_angle := 0.0
var _initial_scale := Vector2.ONE
var _initial_rotation := 0.0


func reset() -> void:
	_touch_positions.clear()
	_initial_distance = 0.0


func handle_event(event: InputEvent, target: Node2D) -> bool:
	if target == null:
		return false
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed:
			_touch_positions[touch.index] = touch.position
			if _touch_positions.size() == 2:
				_begin_transform_gesture(target)
		else:
			_touch_positions.erase(touch.index)
			if _touch_positions.size() == 1:
				var remaining_index = _touch_positions.keys()[0]
				_touch_positions[remaining_index] = _touch_positions[remaining_index]
			elif _touch_positions.is_empty():
				_initial_distance = 0.0
		return true
	if event is InputEventScreenDrag:
		var drag := event as InputEventScreenDrag
		if not _touch_positions.has(drag.index):
			return false
		var previous: Vector2 = _touch_positions[drag.index]
		_touch_positions[drag.index] = drag.position
		if _touch_positions.size() == 1:
			var movement := drag.screen_relative
			if movement.is_zero_approx():
				movement = drag.relative
			if movement.is_zero_approx():
				movement = drag.position - previous
			target.position += movement
		elif _touch_positions.size() >= 2 and _initial_distance > 0.001:
			_apply_transform_gesture(target)
		return true
	return false


func sync_scene_entry(entry: Dictionary, target: Node2D) -> void:
	if entry == null or target == null:
		return
	entry["position"] = [target.position.x / 100.0, -target.position.y / 100.0, 0.0]
	entry["rotation_degrees"] = [0.0, 0.0, target.rotation_degrees]
	entry["scale"] = [target.scale.x, target.scale.y, 1.0]


func _begin_transform_gesture(target: Node2D) -> void:
	var positions := _two_positions()
	if positions.size() < 2:
		return
	var vector: Vector2 = positions[1] - positions[0]
	_initial_distance = maxf(vector.length(), 0.001)
	_initial_angle = vector.angle()
	_initial_scale = target.scale
	_initial_rotation = target.rotation


func _apply_transform_gesture(target: Node2D) -> void:
	var positions := _two_positions()
	if positions.size() < 2:
		return
	var vector: Vector2 = positions[1] - positions[0]
	var distance := maxf(vector.length(), 0.001)
	var factor := distance / _initial_distance
	target.scale = Vector2(
		clampf(_initial_scale.x * factor, MIN_SCALE, MAX_SCALE),
		clampf(_initial_scale.y * factor, MIN_SCALE, MAX_SCALE)
	)
	target.rotation = _initial_rotation + wrapf(vector.angle() - _initial_angle, -PI, PI)


func _two_positions() -> Array[Vector2]:
	var indices: Array = _touch_positions.keys()
	indices.sort()
	var positions: Array[Vector2] = []
	for index in indices:
		positions.append(_touch_positions[index])
	return positions
