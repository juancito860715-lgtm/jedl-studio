extends SceneTree

# Recovery regression suite for ProjectStore. All fixtures use isolated recovery_* IDs.

const ProjectStoreScript = preload("res://scripts/ProjectStore.gd")
const IDS := ["recovery_a", "recovery_b", "recovery_copy"]
var _failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	_clean()
	_test_temp_write_failure_keeps_original()
	_test_replace_failure_keeps_original()
	_test_new_project_final_rename_failure_reports_error()
	_test_whitespace_document_is_rejected()
	_test_interrupted_save_recovers_last_valid_version()
	_test_truncated_main_is_not_loaded_and_backup_can_be_restored()
	_test_restore_without_valid_backup_changes_nothing()
	_test_duplicate_preserves_scene_and_timeline_exactly()
	_test_corrupt_old_file_aborts_save_and_is_preserved()
	_test_valid_main_discards_stale_old()
	_test_corrupt_main_is_promoted_from_valid_old()
	_test_corrupt_old_aborts_and_is_preserved()
	_test_duplicate_refuses_destination_with_pending_valid_old()
	_test_corrupt_diagnostics_never_overwrite_each_other()
	_clean()
	if _failures.is_empty():
		print("PROJECT_STORE_RECOVERY_TEST_OK (14 tests)")
		quit(0)
	else:
		for failure in _failures:
			push_error(failure)
		quit(1)


func _test_temp_write_failure_keeps_original() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Original", _sample_scene("original"), _sample_timeline()), "Initial save succeeds")
	DirAccess.make_dir_absolute(_global(_path("recovery_a", "json") + ".tmp"))
	_check(not ProjectStoreScript.save_project("recovery_a", "Changed", _sample_scene("changed"), _sample_timeline()), "Blocked temp path makes save fail")
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Original", "Original remains readable after temp failure")
	_clean()


func _test_replace_failure_keeps_original() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Original", _sample_scene("original"), _sample_timeline()), "Initial save succeeds")
	ProjectStoreScript.simulate_rename_failure = true
	_check(not ProjectStoreScript.save_project("recovery_a", "Changed", _sample_scene("changed"), _sample_timeline()), "Injected rename failure is reported")
	ProjectStoreScript.simulate_rename_failure = false
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Original", "Original remains readable after rename failure")
	_clean()


func _test_new_project_final_rename_failure_reports_error() -> void:
	_clean()
	ProjectStoreScript.simulate_final_rename_failure = true
	_check(not ProjectStoreScript.save_project("recovery_a", "Nuevo", _sample_scene("n"), _sample_timeline()), "Final rename failure on a new project must report failure")
	ProjectStoreScript.simulate_final_rename_failure = false
	_check(not FileAccess.file_exists(_path("recovery_a", "json")), "No partial file may remain after a failed first save")
	_check(not FileAccess.file_exists(_path("recovery_a", "json.tmp")), "Temporary file is removed after failed first save")
	_clean()


func _test_whitespace_document_is_rejected() -> void:
	_check(ProjectStoreScript._read_document_from_text("   \n\t  ", "recovery_a").is_empty(), "Whitespace-only project document is rejected")


func _test_interrupted_save_recovers_last_valid_version() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Last valid", _sample_scene("valid"), _sample_timeline()), "Initial save succeeds")
	DirAccess.rename_absolute(_global(_path("recovery_a", "json")), _global(_path("recovery_a", "json.old")))
	_check(not ProjectStoreScript.load_project("recovery_a").is_empty(), "Load recovers a valid .old swap")
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Last valid", "Recovered version is the last valid version")
	_clean()


func _test_truncated_main_is_not_loaded_and_backup_can_be_restored() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "First", _sample_scene("first"), _sample_timeline()), "First save succeeds")
	_check(ProjectStoreScript.save_project("recovery_a", "Second", _sample_scene("second"), _sample_timeline()), "Second save succeeds and creates backup")
	var corrupt := FileAccess.open(_path("recovery_a", "json"), FileAccess.WRITE)
	if corrupt != null:
		corrupt.store_string("{\"schemaVersion\": 1, \"ti")
		corrupt.close()
	_check(ProjectStoreScript.load_project("recovery_a").is_empty(), "Truncated main document is rejected")
	var restored := ProjectStoreScript.restore_project("recovery_a")
	_check(not restored.is_empty() and restored.get("title", "") == "First", "Valid backup restores the previous version")
	_clean()


func _test_restore_without_valid_backup_changes_nothing() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Only version", _sample_scene("only"), _sample_timeline()), "Initial save succeeds")
	_check(ProjectStoreScript.restore_project("recovery_a").is_empty(), "Restore without backup is rejected")
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Only version", "Main project remains unchanged")
	var bad := FileAccess.open(_path("recovery_a", "backup.json"), FileAccess.WRITE)
	if bad != null:
		bad.store_string("not-json")
		bad.close()
	_check(ProjectStoreScript.restore_project("recovery_a").is_empty(), "Corrupt backup is rejected")
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Only version", "Corrupt backup does not change main")
	_clean()


func _test_duplicate_preserves_scene_and_timeline_exactly() -> void:
	_clean()
	var scene := _sample_scene("roundtrip")
	var timeline := _sample_timeline()
	_check(ProjectStoreScript.save_project("recovery_a", "Source", scene, timeline), "Source save succeeds")
	_check(ProjectStoreScript.duplicate_project("recovery_a", "recovery_copy", "Copy"), "Duplicate succeeds")
	var copied := ProjectStoreScript.load_project("recovery_copy")
	_check(copied.get("scene", {}) == _normalized(scene), "Duplicate preserves scene exactly")
	_check(copied.get("timeline", {}) == _normalized(timeline), "Duplicate preserves timeline exactly")
	_check(ProjectStoreScript.load_project("recovery_a").get("projectId", "") == "recovery_a", "Source identity is unchanged")
	_clean()


func _test_corrupt_old_file_aborts_save_and_is_preserved() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Original", _sample_scene("v1"), _sample_timeline()), "Initial save succeeds")
	var old := FileAccess.open(_path("recovery_a", "json.old"), FileAccess.WRITE)
	if old != null:
		old.store_string("{broken")
		old.close()
	_check(not ProjectStoreScript.save_project("recovery_a", "Changed", _sample_scene("v2"), _sample_timeline()), "Corrupt pending .old blocks save")
	_check(FileAccess.file_exists(_path("recovery_a", "json.old")), "Corrupt .old evidence is preserved")
	_clean()


func _test_valid_main_discards_stale_old() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Current", _sample_scene("current"), _sample_timeline()), "Initial save succeeds")
	var old_document := _document("recovery_a", "Stale", _sample_scene("stale"), _sample_timeline())
	_write(_path("recovery_a", "json.old"), JSON.stringify(old_document))
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Current", "Valid main remains authoritative")
	_check(not FileAccess.file_exists(_path("recovery_a", "json.old")), "Stale .old is discarded")
	_clean()


func _test_corrupt_main_is_promoted_from_valid_old() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Recovered", _sample_scene("recovered"), _sample_timeline()), "Initial save succeeds")
	DirAccess.rename_absolute(_global(_path("recovery_a", "json")), _global(_path("recovery_a", "json.old")))
	_write(_path("recovery_a", "json"), "{truncated")
	_check(ProjectStoreScript.load_project("recovery_a").get("title", "") == "Recovered", "Valid .old is promoted over corrupt main")
	_check(not FileAccess.file_exists(_path("recovery_a", "json.old")), "Promoted .old path is consumed")
	_clean()


func _test_corrupt_old_aborts_and_is_preserved() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Current", _sample_scene("current"), _sample_timeline()), "Initial save succeeds")
	_write(_path("recovery_a", "json.old"), "{invalid-old")
	_check(ProjectStoreScript.load_project("recovery_a").is_empty(), "Recovery refuses corrupt .old")
	_check(FileAccess.file_exists(_path("recovery_a", "json.old")), "Corrupt .old remains available for diagnosis")
	_clean()


func _test_duplicate_refuses_destination_with_pending_valid_old() -> void:
	_clean()
	_check(ProjectStoreScript.save_project("recovery_a", "Source", _sample_scene("source"), _sample_timeline()), "Source save succeeds")
	_write(_path("recovery_copy", "json.old"), JSON.stringify(_document("recovery_copy", "Pending", _sample_scene("pending"), _sample_timeline())))
	_check(not ProjectStoreScript.duplicate_project("recovery_a", "recovery_copy", "Copy"), "Duplicate refuses destination with pending .old")
	_check(FileAccess.file_exists(_path("recovery_copy", "json.old")), "Destination pending .old is preserved")
	_clean()


func _test_corrupt_diagnostics_never_overwrite_each_other() -> void:
	_clean()
	for round in range(2):
		_check(ProjectStoreScript.save_project("recovery_a", "Valid %d" % round, _sample_scene("v%d" % round), _sample_timeline()), "Save succeeds in recovery round %d" % round)
		DirAccess.rename_absolute(_global(_path("recovery_a", "json")), _global(_path("recovery_a", "json.old")))
		_write(_path("recovery_a", "json"), "{\"schemaVersion\": 1, \"ti")
		_check(not ProjectStoreScript.load_project("recovery_a").is_empty(), "Recovery succeeds in round %d" % round)
	var diagnostics: Array[String] = []
	for file_name in DirAccess.get_files_at(ProjectStoreScript.PROJECT_DIRECTORY):
		if file_name.begins_with("recovery_a.json.corrupt-"):
			diagnostics.append(file_name)
	_check(diagnostics.size() == 2, "Each corrupt main file gets its own diagnostic file")
	for diagnostic in diagnostics:
		_check(_read(ProjectStoreScript.PROJECT_DIRECTORY + "/" + diagnostic).begins_with("{\"schemaVersion\": 1, \"ti"), "Diagnostic content is preserved")
	_clean()


func _clean() -> void:
	ProjectStoreScript.simulate_rename_failure = false
	ProjectStoreScript.simulate_final_rename_failure = false
	# get_files_at() does not enumerate directories. The temp-write failure
	# test deliberately creates recovery_a.json.tmp as a directory, so clean
	# both files and directories to keep every test isolated.
	for file_name in DirAccess.get_files_at(ProjectStoreScript.PROJECT_DIRECTORY):
		if file_name.begins_with("recovery_"):
			DirAccess.remove_absolute(_global(ProjectStoreScript.PROJECT_DIRECTORY + "/" + file_name))
	for directory_name in DirAccess.get_directories_at(ProjectStoreScript.PROJECT_DIRECTORY):
		if directory_name.begins_with("recovery_"):
			DirAccess.remove_absolute(_global(ProjectStoreScript.PROJECT_DIRECTORY + "/" + directory_name))


func _sample_scene(version: String) -> Dictionary:
	return {"version": 2, "title": version, "objects": [{"id": "object", "position": [1.0, 2.0, 3.0]}]}


func _sample_timeline() -> Dictionary:
	return {"schemaVersion": 1, "duration": 1.0, "tracks": [{"target_id": "object", "keyframes": [{"time": 0.0, "value": [0.0, 0.0, 0.0]}, {"time": 1.0, "value": [1.0, 1.0, 1.0]}]}]}


func _document(project_id: String, title: String, scene: Dictionary, timeline: Dictionary) -> Dictionary:
	return {"schemaVersion": 1, "projectId": project_id, "title": title, "scene": scene, "timeline": timeline}


func _normalized(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value))


func _path(project_id: String, suffix: String) -> String:
	return ProjectStoreScript.PROJECT_DIRECTORY + "/" + project_id + "." + suffix


func _global(path: String) -> String:
	return ProjectSettings.globalize_path(path)


func _write(path: String, content: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file != null:
		file.store_string(content)
		file.close()


func _read(path: String) -> String:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var content := file.get_as_text()
	file.close()
	return content


func _check(condition: bool, message: String) -> void:
	if not condition:
		_failures.append(message)
