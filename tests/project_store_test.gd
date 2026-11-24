extends SceneTree

const ProjectStoreScript = preload("res://scripts/ProjectStore.gd")


func _initialize() -> void:
	call_deferred("_run_tests")


func _run_tests() -> void:
	var scene := {
		"version": 2,
		"title": "Round trip",
		"characters": [{"id": "actor", "assetId": "character.jedl.starter.v1"}],
		"objects": [],
		"subtitles": [],
		"sounds": [],
		"actions": [{"target": "actor", "property": "position", "time": 0.0, "duration": 1.0, "to": [1.0, 0.0, 0.0]}]
	}
	var timeline := {
		"schemaVersion": 1,
		"duration": 1.0,
		"tracks": [{"target_id": "actor", "property": "position", "keyframes": [
			{"time": 0.0, "value": [0.0, 0.0, 0.0]},
			{"time": 1.0, "value": [1.0, 0.0, 0.0]}
		]}]
	}
	assert(ProjectStoreScript.save_project("hito1roundtrip", "Proyecto de prueba", scene, timeline), "Project must save to user://")
	var loaded := ProjectStoreScript.load_project("hito1roundtrip")
	assert(not loaded.is_empty(), "Saved project must load")
	assert(loaded["scene"] == _normalized_json(scene), "Scene data must survive an exact JSON round trip")
	assert(loaded["timeline"] == _normalized_json(timeline), "Animation data must survive an exact JSON round trip")

	var changed_scene := scene.duplicate(true)
	changed_scene["title"] = "Modified"
	assert(ProjectStoreScript.save_project("hito1roundtrip", "Proyecto modificado", changed_scene, timeline), "Second save must create a restorable backup")
	var restored := ProjectStoreScript.restore_project("hito1roundtrip")
	assert(not restored.is_empty(), "Previous project version must be restorable")
	assert(restored["scene"] == _normalized_json(scene), "Restore must recover the previous scene exactly")
	assert(ProjectStoreScript.duplicate_project("hito1roundtrip", "hito1copy", "Copia"), "Project must be duplicable")
	var copy := ProjectStoreScript.load_project("hito1copy")
	assert(copy["projectId"] == "hito1copy" and copy["title"] == "Copia", "Duplicate must have its own identity and title")
	assert(copy["scene"] == _normalized_json(scene) and copy["timeline"] == _normalized_json(timeline), "Duplicate must preserve scene and animation")

	print("PROJECT_STORE_TEST_OK")
	quit(0)


func _normalized_json(value: Variant) -> Variant:
	return JSON.parse_string(JSON.stringify(value))
