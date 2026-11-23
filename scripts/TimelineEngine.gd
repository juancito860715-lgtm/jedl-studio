extends Node
class_name TimelineEngine

signal playhead_changed(seconds: float)
signal playback_finished

const EPSILON := 0.0001
const SUPPORTED_PROPERTIES := ["position", "rotation_degrees", "scale"]

var _targets: Dictionary = {}
var _tracks: Array[Dictionary] = []
var duration_seconds := 0.0
var playhead_seconds := 0.0
var is_playing := false
var is_paused := false
var loop_enabled := false
var last_error := ""


func register_target(target_id: String, target: Node3D) -> bool:
	if target_id.strip_edges().is_empty() or target == null:
		return false
	_targets[target_id] = target
	return true


func clear_targets() -> void:
	_targets.clear()


func clear_timeline() -> void:
	_tracks.clear()
	duration_seconds = 0.0
	playhead_seconds = 0.0
	is_playing = false
	is_paused = false
	last_error = ""


func compile_json_actions(actions: Array) -> bool:
	last_error = ""
	var ordered: Array = actions.duplicate(true)
	ordered.sort_custom(func(a: Variant, b: Variant) -> bool:
		if not (a is Dictionary) or not (b is Dictionary):
			return false
		return float(a.get("time", 0.0)) < float(b.get("time", 0.0))
	)

	var candidate: Dictionary = {}
	var last_end: Dictionary = {}
	var last_value: Dictionary = {}
	for action_value in ordered:
		if not (action_value is Dictionary):
			return _fail("Cada acción JSON debe ser un objeto.")
		var action: Dictionary = action_value
		var target_id := String(action.get("target", action.get("targetId", "")))
		var property_name := _normalize_property(String(action.get("property", "")))
		var start_time := float(action.get("time", -1.0))
		var action_duration := float(action.get("duration", 0.0))
		var parsed_end_value: Variant = _vector_from(action.get("to", null))
		if not (parsed_end_value is Vector3):
			return _fail("La acción requiere un vector 'to' de tres números.")
		var end_value: Vector3 = parsed_end_value
		if target_id.is_empty() or not _targets.has(target_id):
			return _fail("La acción apunta a un elemento inexistente: " + target_id)
		if not SUPPORTED_PROPERTIES.has(property_name):
			return _fail("Propiedad de animación no soportada: " + property_name)
		if start_time < 0.0 or action_duration <= 0.0:
			return _fail("Cada acción requiere time >= 0 y duration > 0.")
		var track_id := target_id + "|" + property_name
		if last_end.has(track_id) and start_time < float(last_end[track_id]) - EPSILON:
			return _fail("Hay acciones solapadas para " + target_id + " / " + property_name)
		var target := _targets[target_id] as Node3D
		var start_value: Vector3 = last_value[track_id] if last_value.has(track_id) else _read_property(target, property_name)
		if action.has("from"):
			var parsed_from: Variant = _vector_from(action["from"])
			if not (parsed_from is Vector3):
				return _fail("El campo 'from' debe contener tres números.")
			var explicit_from: Vector3 = parsed_from
			start_value = explicit_from
		if not candidate.has(track_id):
			candidate[track_id] = {
				"target_id": target_id,
				"property": property_name,
				"keyframes": []
			}
		var keys: Array = candidate[track_id]["keyframes"]
		_upsert_compiled_keyframe(keys, start_time, start_value)
		_upsert_compiled_keyframe(keys, start_time + action_duration, end_value)
		last_end[track_id] = start_time + action_duration
		last_value[track_id] = end_value

	var compiled: Array[Dictionary] = []
	for track_value in candidate.values():
		var track: Dictionary = track_value
		track["keyframes"].sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
			return float(a["time"]) < float(b["time"])
		)
		compiled.append(track)
	_tracks = compiled
	_recalculate_duration()
	seek(0.0)
	return true


func add_keyframe(target_id: String, property_name: String, time_seconds: float, value: Vector3) -> bool:
	last_error = ""
	property_name = _normalize_property(property_name)
	if not _targets.has(target_id):
		return _fail("No existe el elemento seleccionado: " + target_id)
	if not SUPPORTED_PROPERTIES.has(property_name):
		return _fail("Propiedad no soportada: " + property_name)
	if time_seconds < 0.0:
		return _fail("El tiempo del keyframe no puede ser negativo.")
	var track := _get_or_create_track(target_id, property_name)
	var keys: Array = track["keyframes"]
	for key_index in range(keys.size()):
		if absf(float(keys[key_index]["time"]) - time_seconds) <= EPSILON:
			keys[key_index]["value"] = _vector_to_array(value)
			_recalculate_duration()
			seek(playhead_seconds)
			return true
	keys.append({"time": time_seconds, "value": _vector_to_array(value)})
	keys.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a["time"]) < float(b["time"])
	)
	_recalculate_duration()
	seek(playhead_seconds)
	return true


func move_keyframe(target_id: String, property_name: String, old_time: float, new_time: float) -> bool:
	var track := _find_track(target_id, _normalize_property(property_name))
	if track.is_empty() or new_time < 0.0:
		return _fail("No se encontró el keyframe o el nuevo tiempo es inválido.")
	var keys: Array = track["keyframes"]
	for key_value in keys:
		if absf(float(key_value["time"]) - old_time) <= EPSILON:
			for other in keys:
				if other != key_value and absf(float(other["time"]) - new_time) <= EPSILON:
					return _fail("Ya existe un keyframe en ese instante.")
			key_value["time"] = new_time
			keys.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
				return float(a["time"]) < float(b["time"])
			)
			_recalculate_duration()
			seek(playhead_seconds)
			return true
	return _fail("No se encontró el keyframe que se desea mover.")


func edit_keyframe(target_id: String, property_name: String, time_seconds: float, value: Vector3) -> bool:
	var track := _find_track(target_id, _normalize_property(property_name))
	if track.is_empty():
		return _fail("No se encontró la pista del keyframe.")
	for key_value in track["keyframes"]:
		if absf(float(key_value["time"]) - time_seconds) <= EPSILON:
			key_value["value"] = _vector_to_array(value)
			seek(playhead_seconds)
			return true
	return _fail("No se encontró el keyframe que se desea editar.")


func delete_keyframe(target_id: String, property_name: String, time_seconds: float) -> bool:
	var track_index := _find_track_index(target_id, _normalize_property(property_name))
	if track_index < 0:
		return _fail("No se encontró la pista del keyframe.")
	var keys: Array = _tracks[track_index]["keyframes"]
	for key_index in range(keys.size()):
		if absf(float(keys[key_index]["time"]) - time_seconds) <= EPSILON:
			keys.remove_at(key_index)
			if keys.is_empty():
				_tracks.remove_at(track_index)
			_recalculate_duration()
			seek(playhead_seconds)
			return true
	return _fail("No se encontró el keyframe que se desea eliminar.")


func play() -> void:
	if duration_seconds <= 0.0:
		is_playing = false
		is_paused = false
		return
	if playhead_seconds >= duration_seconds - EPSILON:
		playhead_seconds = 0.0
	_apply_at(playhead_seconds)
	is_paused = false
	is_playing = true
	set_process(true)


func pause() -> void:
	if is_playing:
		is_playing = false
		is_paused = true
		set_process(false)


func resume() -> void:
	if is_paused and duration_seconds > 0.0:
		is_paused = false
		is_playing = true
		set_process(true)


func stop() -> void:
	is_playing = false
	is_paused = false
	set_process(false)
	playhead_seconds = 0.0
	_apply_at(0.0)
	playhead_changed.emit(playhead_seconds)


func seek(time_seconds: float) -> void:
	playhead_seconds = clampf(time_seconds, 0.0, duration_seconds)
	_apply_at(playhead_seconds)
	playhead_changed.emit(playhead_seconds)


func get_keyframe_count() -> int:
	var total := 0
	for track in _tracks:
		total += (track["keyframes"] as Array).size()
	return total


func to_dictionary() -> Dictionary:
	var output_tracks: Array[Dictionary] = []
	for track in _tracks:
		output_tracks.append({
			"target_id": String(track["target_id"]),
			"property": String(track["property"]),
			"keyframes": (track["keyframes"] as Array).duplicate(true)
		})
	return {
		"schemaVersion": 1,
		"duration": duration_seconds,
		"tracks": output_tracks
	}


func load_dictionary(data: Dictionary) -> bool:
	last_error = ""
	if int(data.get("schemaVersion", -1)) != 1 or not (data.get("tracks", null) is Array):
		return _fail("Formato de timeline no compatible.")
	var candidate: Array[Dictionary] = []
	for track_value in data["tracks"]:
		if not (track_value is Dictionary):
			return _fail("Pista de timeline inválida.")
		var track: Dictionary = track_value
		var target_id := String(track.get("target_id", ""))
		var property_name := _normalize_property(String(track.get("property", "")))
		var keys_value: Variant = track.get("keyframes", null)
		if not _targets.has(target_id) or not SUPPORTED_PROPERTIES.has(property_name) or not (keys_value is Array):
			return _fail("Pista sin destino válido o sin keyframes.")
		var keys: Array[Dictionary] = []
		for key_value in keys_value:
			if not (key_value is Dictionary):
				return _fail("Keyframe inválido.")
			var key: Dictionary = key_value
			var parsed_vector: Variant = _vector_from(key.get("value", null))
			var time_value := float(key.get("time", -1.0))
			if not (parsed_vector is Vector3) or time_value < 0.0:
				return _fail("Keyframe con tiempo o valor inválido.")
			var vector: Vector3 = parsed_vector
			keys.append({"time": time_value, "value": _vector_to_array(vector)})
		keys.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
			return float(a["time"]) < float(b["time"])
		)
		candidate.append({"target_id": target_id, "property": property_name, "keyframes": keys})
	_tracks = candidate
	_recalculate_duration()
	seek(0.0)
	return true


func _process(delta: float) -> void:
	if not is_playing:
		return
	playhead_seconds += delta
	if playhead_seconds >= duration_seconds:
		if loop_enabled and duration_seconds > 0.0:
			playhead_seconds = fposmod(playhead_seconds, duration_seconds)
		else:
			playhead_seconds = duration_seconds
			_apply_at(playhead_seconds)
			is_playing = false
			set_process(false)
			playhead_changed.emit(playhead_seconds)
			playback_finished.emit()
			return
	_apply_at(playhead_seconds)
	playhead_changed.emit(playhead_seconds)


func _upsert_compiled_keyframe(keys: Array, time_seconds: float, value: Vector3) -> void:
	for key_value in keys:
		if absf(float(key_value["time"]) - time_seconds) <= EPSILON:
			key_value["time"] = time_seconds
			key_value["value"] = _vector_to_array(value)
			return
	keys.append({"time": time_seconds, "value": _vector_to_array(value)})


func _get_or_create_track(target_id: String, property_name: String) -> Dictionary:
	var existing := _find_track(target_id, property_name)
	if not existing.is_empty():
		return existing
	var created := {"target_id": target_id, "property": property_name, "keyframes": []}
	_tracks.append(created)
	return created


func _find_track(target_id: String, property_name: String) -> Dictionary:
	var index := _find_track_index(target_id, property_name)
	return _tracks[index] if index >= 0 else {}


func _find_track_index(target_id: String, property_name: String) -> int:
	for index in range(_tracks.size()):
		if String(_tracks[index]["target_id"]) == target_id and String(_tracks[index]["property"]) == property_name:
			return index
	return -1


func _normalize_property(property_name: String) -> String:
	if property_name == "rotation":
		return "rotation_degrees"
	return property_name


func _vector_from(value: Variant) -> Variant:
	if value is Vector3:
		return value
	if value is Array and value.size() >= 3:
		return Vector3(float(value[0]), float(value[1]), float(value[2]))
	return null


func _vector_to_array(value: Vector3) -> Array:
	return [value.x, value.y, value.z]


func _read_property(target: Node3D, property_name: String) -> Vector3:
	match property_name:
		"position":
			return target.position
		"rotation_degrees":
			return target.rotation_degrees
		"scale":
			return target.scale
	return Vector3.ZERO


func _write_property(target: Node3D, property_name: String, value: Vector3) -> void:
	match property_name:
		"position":
			target.position = value
		"rotation_degrees":
			target.rotation_degrees = value
		"scale":
			target.scale = value


func _apply_at(time_seconds: float) -> void:
	for track in _tracks:
		var target_id := String(track["target_id"])
		if not _targets.has(target_id):
			continue
		var target := _targets[target_id] as Node3D
		if not is_instance_valid(target):
			continue
		var keys: Array = track["keyframes"]
		if keys.is_empty():
			continue
		var value: Vector3 = _vector_from(keys[0]["value"])
		if time_seconds >= float(keys.back()["time"]):
			value = _vector_from(keys.back()["value"])
		elif time_seconds > float(keys[0]["time"]):
			for index in range(keys.size() - 1):
				var left: Dictionary = keys[index]
				var right: Dictionary = keys[index + 1]
				var left_time := float(left["time"])
				var right_time := float(right["time"])
				if time_seconds >= left_time and time_seconds <= right_time and right_time - left_time > EPSILON:
					var left_value: Vector3 = _vector_from(left["value"])
					var right_value: Vector3 = _vector_from(right["value"])
					var weight := clampf((time_seconds - left_time) / (right_time - left_time), 0.0, 1.0)
					value = left_value.lerp(right_value, weight)
					break
		_write_property(target, String(track["property"]), value)


func _recalculate_duration() -> void:
	duration_seconds = 0.0
	for track in _tracks:
		for key in track["keyframes"]:
			duration_seconds = maxf(duration_seconds, float(key["time"]))
	playhead_seconds = clampf(playhead_seconds, 0.0, duration_seconds)


func _fail(message: String) -> bool:
	last_error = message
	push_error(message)
	return false
