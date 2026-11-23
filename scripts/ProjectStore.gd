extends RefCounted
class_name ProjectStore

const SCHEMA_VERSION := 1
const PROJECT_DIRECTORY := "user://projects"


static func save_project(project_id: String, title: String, scene_data: Dictionary, timeline_data: Dictionary) -> bool:
	if not _valid_id(project_id):
		return false
	if DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PROJECT_DIRECTORY)) != OK:
		return false
	var path := _project_path(project_id, "json")
	if FileAccess.file_exists(path):
		var previous := _read_text(path)
		if previous.is_empty() or not _write_text(_project_path(project_id, "backup.json"), previous):
			return false
	var document := {
		"schemaVersion": SCHEMA_VERSION,
		"projectId": project_id,
		"title": title,
		"scene": scene_data.duplicate(true),
		"timeline": timeline_data.duplicate(true)
	}
	return _write_text(path, JSON.stringify(document, "\t", true, true) + "\n")


static func load_project(project_id: String) -> Dictionary:
	if not _valid_id(project_id):
		return {}
	var document := _read_document(_project_path(project_id, "json"))
	return document


static func duplicate_project(source_id: String, destination_id: String, new_title: String = "") -> bool:
	if not _valid_id(destination_id) or FileAccess.file_exists(_project_path(destination_id, "json")):
		return false
	var source := load_project(source_id)
	if source.is_empty():
		return false
	source["projectId"] = destination_id
	if not new_title.is_empty():
		source["title"] = new_title
	return _write_text(_project_path(destination_id, "json"), JSON.stringify(source, "\t", true, true) + "\n")


static func restore_project(project_id: String) -> Dictionary:
	if not _valid_id(project_id):
		return {}
	var backup_path := _project_path(project_id, "backup.json")
	var document := _read_document(backup_path)
	if document.is_empty():
		return {}
	var backup_text := _read_text(backup_path)
	if not _write_text(_project_path(project_id, "json"), backup_text):
		return {}
	return document


static func _read_document(path: String) -> Dictionary:
	var content := _read_text(path)
	if content.is_empty():
		return {}
	var parsed: Variant = JSON.parse_string(content)
	if not parsed is Dictionary or int(parsed.get("schemaVersion", -1)) != SCHEMA_VERSION:
		return {}
	if not parsed.get("scene", null) is Dictionary or not parsed.get("timeline", null) is Dictionary:
		return {}
	return parsed


static func _read_text(path: String) -> String:
	if not FileAccess.file_exists(path):
		return ""
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var content := file.get_as_text()
	file.close()
	return content


static func _write_text(path: String, content: String) -> bool:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(content)
	file.close()
	return true


static func _project_path(project_id: String, suffix: String) -> String:
	return PROJECT_DIRECTORY + "/" + project_id + "." + suffix


static func _valid_id(project_id: String) -> bool:
	if project_id.is_empty() or project_id.length() > 64:
		return false
	for character in project_id:
		if not (character.is_valid_identifier() or character == "-"):
			return false
	return true
