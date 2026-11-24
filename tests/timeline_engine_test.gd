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
		{"target": "actor", "property": "rotation_degrees", "time": 0.0, "duration": 2.0, "to": [0.0, 90.0, 0.0]},
		{"target": "actor", "property": "scale", "time": 0.0, "duration": 2.0, "to": [2.0, 1.0, 1.0]}
	]
	assert(json_engine.compile_json_actions(actions), "JSON actions must compile into the shared timeline")
	assert(json_engine.get_keyframe_count() == 7, "Adjacent JSON actions must share one boundary keyframe instead of creating duplicate-time keys")
	assert(manual_engine.add_keyframe("actor", "position", 0.0, Vector3.ZERO), "Manual initial keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "position", 1.0, Vector3(1.0, 0.0, 0.0)), "Manual middle keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "position", 2.0, Vector3(2.0, 0.0, 0.0)), "Manual final keyframe must be accepted")
	assert(manual_engine.add_keyframe("actor", "rotation_degrees", 0.0, Vector3.ZERO), "Manual rotation start must be accepted")
	assert(manual_engine.add_keyframe("actor", "rotation_degrees", 2.0, Vector3(0.0, 90.0, 0.0)), "Manual rotation end must be accepted")
	assert(manual_engine.add_keyframe("actor", "scale", 0.0, Vector3.ONE), "Manual scale start must be accepted")
	assert(manual_engine.add_keyframe("actor", "scale", 2.0, Vector3(2.0, 1.0, 1.0)), "Manual scale end must be accepted")

	for sample_time in [0.0, 0.5, 1.0, 1.5, 2.0]:
		json_engine.seek(sample_time)
		manual_engine.seek(sample_time)
		assert(json_target.position.is_equal_approx(manual_target.position), "JSON/manual position must match at %.2f" % sample_time)
		assert(json_target.rotation_degrees.is_equal_approx(manual_target.rotation_degrees), "JSON/manual rotation must match at %.2f" % sample_time)
		assert(json_target.scale.is_equal_approx(manual_target.scale), "JSON/manual scale must match at %.2f" % sample_time)

	json_engine.seek(1.5)
	assert(json_target.position.is_equal_approx(Vector3(1.5, 0.0, 0.0)), "Consecutive actions must interpolate after their shared boundary")
	assert(json_target.rotation_degrees.is_equal_approx(Vector3(0.0, 67.5, 0.0)), "Different properties must animate concurrently")
	assert(json_target.scale.is_equal_approx(Vector3(1.75, 1.0, 1.0)), "Scale actions must interpolate through the shared engine")

	assert(manual_engine.move_keyframe("actor", "position", 1.0, 1.25), "Keyframes must be movable")
	assert(manual_engine.edit_keyframe("actor", "position", 1.25, Vector3(1.25, 0.0, 0.0)), "Keyframes must be editable")
	assert(manual_engine.delete_keyframe("actor", "position", 1.25), "Keyframes must be deletable")

	var invalid_overlap := [
		{"target": "actor", "property": "position", "time": 0.0, "duration": 2.0, "to": [1.0, 0.0, 0.0]},
		{"target": "actor", "property": "position", "time": 1.0, "duration": 1.0, "to": [2.0, 0.0, 0.0]}
	]
	assert(not json_engine.compile_json_actions(invalid_overlap), "Overlapping actions on the same property must be rejected")

	assert(json_engine.compile_json_actions(actions), "Valid JSON timeline must compile again")
	var serialized: Dictionary = json_engine.to_dictionary()
	var restored_target := Node3D.new()
	root.add_child(restored_target)
	var restored_engine = TimelineScript.new()
	root.add_child(restored_engine)
	restored_engine.register_target("actor", restored_target)
	assert(restored_engine.load_dictionary(serialized), "Serialized timeline must load into a fresh engine")
	assert(restored_engine.to_dictionary() == serialized, "Timeline serialization must survive an exact round trip")
	for sample_time in [0.0, 0.25, 0.75, 1.0, 1.5, 1.9, 2.0]:
		json_engine.seek(sample_time)
		restored_engine.seek(sample_time)
		assert(json_target.position.is_equal_approx(restored_target.position), "Restored position must match at %.2f" % sample_time)
		assert(json_target.rotation_degrees.is_equal_approx(restored_target.rotation_degrees), "Restored rotation must match at %.2f" % sample_time)
		assert(json_target.scale.is_equal_approx(restored_target.scale), "Restored scale must match at %.2f" % sample_time)

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
