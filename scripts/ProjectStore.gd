extends RefCounted
class_name ProjectStore

const SCHEMA_VERSION := 1
const PROJECT_DIRECTORY := "user://projects"

# Test seam: simulates failure after the original has been moved to .old.
static var simulate_rename_failure := false


static func save_project(project_id: String, title: String, scene_data: Dictionary, timeline_data: Dictionary) -> bool:
	if not _valid_id(project_id) or not _ensure_directory():
		return false
	if not _recover_interrupted_swap(project_id):
		return false

	var path := _project_path(project_id, "json")
	var current_text := _read_text(path)
	if FileAccess.file_exists(path):
		if current_text.is_empty() or _read_document_from_text(current_text, project_id).is_empty():
			return false
		if not _atomic_write(_backup_path(project_id), current_text, false):
			return false

	var document := {
		"schemaVersion": SCHEMA_VERSION,
		"projectId": project_id,
		"title": title,
		"scene": scene_data.duplicate(true),
		"timeline": timeline_data.duplicate(true)
	}
	return _atomic_write(path, _serialize(document), true)


static func load_project(project_id: String) -> Dictionary:
	if not _valid_id(project_id) or not _ensure_directory():
		return {}
	if not _recover_interrupted_swap(project_id):
		return {}
	return _read_document(_project_path(project_id, "json"), project_id)


static func duplicate_project(source_id: String, destination_id: String, new_title: String = "") -> bool:
	if not _valid_id(source_id) or not _valid_id(destination_id) or source_id == destination_id:
		return false
	if not _ensure_directory():
		return false
	var destination_path := _project_path(destination_id, "json")
	# Never adopt or overwrite a destination that has an interrupted swap pending.
	if FileAccess.file_exists(destination_path) or FileAccess.file_exists(destination_path + ".old"):
		return false
	if not _recover_interrupted_swap(source_id):
		return false

	var source := load_project(source_id)
	if source.is_empty():
		return false
	source["projectId"] = destination_id
	if not new_title.is_empty():
		source["title"] = new_title
	return _atomic_write(destination_path, _serialize(source), false)


static func restore_project(project_id: String) -> Dictionary:
	if not _valid_id(project_id) or not _ensure_directory():
		return {}
	if not _recover_interrupted_swap(project_id):
		return {}
	var backup_path := _backup_path(project_id)
	var backup_text := _read_text(backup_path)
	var document := _read_document_from_text(backup_text, project_id)
	if document.is_empty():
		return {}
	if not _atomic_write(_project_path(project_id, "json"), backup_text, true):
		return {}
	return document


static func _recover_interrupted_swap(project_id: String) -> bool:
	return _recover_path(_project_path(project_id, "json"), project_id) and _recover_path(_backup_path(project_id), project_id)


static func _recover_path(path: String, expected_id: String) -> bool:
	var old_path := path + ".old"
	if not FileAccess.file_exists(old_path):
		return true

	var old_document := _read_document(old_path, expected_id)
	if old_document.is_empty():
		return false

	if FileAccess.file_exists(path):
		var current_document := _read_document(path, expected_id)
		if not current_document.is_empty():
			return DirAccess.remove_absolute(_global(old_path)) == OK

		# Preserve corrupt content under a unique diagnostic name before recovery.
		var corrupt_path := _unique_corrupt_path(path)
		if DirAccess.rename_absolute(_global(path), _global(corrupt_path)) != OK:
			return false

	if DirAccess.rename_absolute(_global(old_path), _global(path)) != OK:
		return false
	return not _read_document(path, expected_id).is_empty()


# Returns a path not occupied by either a file or directory; never overwrites evidence.
static func _unique_corrupt_path(path: String) -> String:
	var stamp := int(Time.get_unix_time_from_system())
	var candidate := "%s.corrupt-%d" % [path, stamp]
	var index := 1
	while FileAccess.file_exists(candidate) or DirAccess.dir_exists_absolute(_global(candidate)):
		candidate = "%s.corrupt-%d-%d" % [path, stamp, index]
		index += 1
	return candidate


static func _atomic_write(path: String, content: String, preserve_old_on_success: bool = true) -> bool:
	var temp_path := path + ".tmp"
	var old_path := path + ".old"
	if FileAccess.file_exists(temp_path) and DirAccess.remove_absolute(_global(temp_path)) != OK:
		return false

	var file := FileAccess.open(temp_path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(content)
	file.close()
	if _read_text(temp_path) != content:
		return false

	if FileAccess.file_exists(old_path):
		if DirAccess.remove_absolute(_global(old_path)) != OK:
			return false

	var had_original := FileAccess.file_exists(path)
	if had_original and DirAccess.rename_absolute(_global(path), _global(old_path)) != OK:
		return false

	if simulate_rename_failure:
		_restore_original(path, temp_path, old_path, had_original)
		return false

	if DirAccess.rename_absolute(_global(temp_path), _global(path)) != OK:
		return _restore_original(path, temp_path, old_path, had_original)
	if _read_text(path) != content:
		return false

	if had_original and not preserve_old_on_success:
		if DirAccess.remove_absolute(_global(old_path)) != OK:
			return false
	elif had_original and preserve_old_on_success:
		# The previous version is retained only until the new file is verified.
		if DirAccess.remove_absolute(_global(old_path)) != OK:
			return false
	return true


static func _restore_original(path: String, temp_path: String, old_path: String, had_original: bool) -> bool:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(_global(path))
	if had_original and FileAccess.file_exists(old_path):
		if DirAccess.rename_absolute(_global(old_path), _global(path)) != OK:
			return false
	if FileAccess.file_exists(temp_path):
		DirAccess.remove_absolute(_global(temp_path))
	return not had_original or FileAccess.file_exists(path)


static func _read_document(path: String, expected_id: String) -> Dictionary:
	return _read_document_from_text(_read_text(path), expected_id)


static func _read_document_from_text(content: String, expected_id: String) -> Dictionary:
	if content.is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(content)
	if not (parsed is Dictionary):
		return {}
	if int(parsed.get("schemaVersion", -1)) != SCHEMA_VERSION:
		return {}
	if str(parsed.get("projectId", "")) != expected_id:
		return {}
	if not (parsed.get("title", null) is String):
		return {}
	if not (parsed.get("scene", null) is Dictionary) or not (parsed.get("timeline", null) is Dictionary):
		return {}
	return parsed


static func _serialize(document: Dictionary) -> String:
	return JSON.stringify(document, "\t", true, true) + "\n"


static func _ensure_directory() -> bool:
	return DirAccess.make_dir_recursive_absolute(_global(PROJECT_DIRECTORY)) == OK or DirAccess.dir_exists_absolute(_global(PROJECT_DIRECTORY))


static func _read_text(path: String) -> String:
	if not FileAccess.file_exists(path):
		return ""
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var content := file.get_as_text()
	file.close()
	return content


static func _global(path: String) -> String:
	return ProjectSettings.globalize_path(path)


static func _project_path(project_id: String, suffix: String) -> String:
	return PROJECT_DIRECTORY + "/" + project_id + "." + suffix


static func _backup_path(project_id: String) -> String:
	return _project_path(project_id, "backup.json")


static func _valid_id(project_id: String) -> bool:
	if project_id.is_empty() or project_id.length() > 64:
		return false
	for index in range(project_id.length()):
		var code := project_id.unicode_at(index)
		var is_letter := (code >= 65 and code <= 90) or (code >= 97 and code <= 122)
		var is_digit := code >= 48 and code <= 57
		if not (is_letter or is_digit or code == 45 or code == 95):
			return false
	return true
