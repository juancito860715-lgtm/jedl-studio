extends SceneTree

const TimelineScript = preload("res://scripts/TimelineEngine.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var json_target := Node3D.new()
	var manual_target := Node3D.new()
	root.add_child(json_target)
	root.add_child(manual_target)
	var json_engine = TimelineScript.new()
	var manual_engine = TimelineScript.new()
	root.add_child(json_engine)
	root.add_child(manual_engine)
	json_engine.register_target("actor", json_target)
	manual_engine.register_target("actor", manual_target)

	var actions := [
		{"target": "actor", "property": "position", "time": 0.0, "duration": 1.0, "to": [1.0, 0.0, 0.0]},
		{"target": "actor", "property": "position", "time": 1.0, "duration": 1.0, "to": [2.0, 0.0, 0.0]},
		{"target": "actor", "property": "rotation_degrees", "time": 0.0, "duration": 2.0, "to": [0.0, 90.0, 0.0]}
	]
	assert(json_engine.compile_json_actions(actions), "JSON actions must compile into the shared timeline")
	assert(manual_engine.add_keyframe("actor", "position", 0.0, Vector3.ZERO), "Manual initial keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "position", 1.0, Vector3(1.0, 0.0, 0.0)), "Manual middle keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "position", 2.0, Vector3(2.0, 0.0, 0.0)), "Manual final keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "rotation_degrees", 0.0, Vector3.ZERO), "Manual rotation start must be accepted")
	assert(manual_engine.add_keyframe("actor", "rotation_degrees", 2.0, Vector3(0.0, 90.0, 0.0)), "Manual rotation end must be accepted")

	json_engine.seek(1.5)
	manual_engine.seek(1.5)
	assert(json_target.position.is_equal_approx(manual_target.position), "JSON and manual keyframes must produce identical position")
	assert(json_target.rotation_degrees.is_equal_approx(manual_target.rotation_degrees), "JSON and manual keyframes must produce identical rotation")
	assert(json_target.position.is_equal_approx(Vector3(1.5, 0.0, 0.0)), "Consecutive actions must interpolate through their shared boundary")
	assert(json_target.rotation_degrees.is_equal_approx(Vector3(0.0, 67.5, 0.0)), "Different properties must animate concurrently")

	assert(manual_engine.move_keyframe("actor", "position", 1.0, 1.25), "Keyframes must be movable")
	assert(manual_engine.edit_keyframe("actor", "position", 1.25, Vector3(1.25, 0.0, 0.0)), "Keyframes must be editable")
	assert(manual_engine.delete_keyframe("actor", "position", 1.25), "Keyframes must be deletable")

	var invalid_overlap := [
		{"target": "actor", "property": "position", "time": 0.0, "duration": 2.0, "to": [1.0, 0.0, 0.0]},
		{"target": "actor", "property": "position", "time": 1.0, "duration": 1.0, "to": [2.0, 0.0, 0.0]}
	]
	assert(not json_engine.compile_json_actions(invalid_overlap), "Overlapping actions on the same property must be rejected")

	json_engine.compile_json_actions(actions)
	json_engine.play()
	json_engine._process(0.5)
	assert(json_engine.is_playing, "Playback must start")
	json_engine.pause()
	assert(json_engine.is_paused and not json_engine.is_playing, "Playback must pause")
	json_engine.resume()
	assert(json_engine.is_playing, "Playback must resume")
	json_engine.seek(0.75)
	assert(is_equal_approx(json_engine.playhead_seconds, 0.75), "The playhead must seek")
	json_engine.stop()
	assert(not json_engine.is_playing and is_zero_approx(json_engine.playhead_seconds), "Stop must reset playback")

	print("TIMELINE_ENGINE_TEST_OK")
	quit(0)
