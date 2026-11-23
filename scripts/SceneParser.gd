extends Node
class_name SceneParser

const TimelineEngineScript = preload("res://scripts/TimelineEngine.gd")

var world_root: Node3D
var canvas_root: Node2D
var camera: Camera3D
var background_sprite: Sprite3D
var subtitle_label: Control
var audio_player: AudioStreamPlayer
var catalog_manager: Node
var scene_data: Dictionary = {}
var active_instances: Array[Node] = []
var _events: Array[Dictionary] = []
var _playing := false
var _playback_time := 0.0
var _next_event := 0
var _active_animation_players: Array[Dictionary] = []
var last_error := ""
var timeline_engine: Node
var last_missing_kind := "3d"
var last_missing_category := ""
var last_missing_entry_id := ""


func _ready() -> void:
	timeline_engine = TimelineEngineScript.new()
	timeline_engine.name = "TimelineEngine"
	add_child(timeline_engine)


func load_scene_file(path: String) -> bool:
	if not FileAccess.file_exists(path):
		push_error("Scene JSON not found: " + path)
		return false
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Cannot open scene JSON: " + path)
		return false
	var source := file.get_as_text()
	file.close()
	return load_scene_text(source)


func load_scene_text(source: String) -> bool:
	last_error = ""
	last_missing_entry_id = ""
	last_missing_category = ""
	last_missing_kind = "3d"
	var json_parser := JSON.new()
	var parse_result := json_parser.parse(source)
	if parse_result != OK:
		last_error = "JSON inválido, línea %d: %s" % [json_parser.get_error_line(), json_parser.get_error_message()]
		push_error(last_error)
		return false
	if typeof(json_parser.data) != TYPE_DICTIONARY:
		last_error = "La raíz del JSON debe ser un objeto { ... }."
		push_error(last_error)
		return false
	var candidate: Dictionary = json_parser.data
	for key in ["characters", "objects", "subtitles", "sounds"]:
		if not candidate.has(key):
			last_error = "Falta el campo obligatorio '%s'." % key
			push_error(last_error)
			return false
		if typeof(candidate[key]) != TYPE_ARRAY:
			last_error = "El campo '%s' debe ser una lista []." % key
			push_error(last_error)
			return false
	if candidate.has("actions") and typeof(candidate["actions"]) != TYPE_ARRAY:
		last_error = "El campo actions debe ser una lista []."
		push_error(last_error)
		return false
	_clear_instances()
	clear_background()
	scene_data = candidate
	_events.clear()
	_playing = false
	_playback_time = 0.0
	_next_event = 0
	var background_data: Variant = scene_data.get("background", {})
	if background_data is Dictionary and not background_data.is_empty():
		var resolved_background := _resolve_scene_entry(background_data)
		if resolved_background.is_empty():
			last_error = "No se pudo resolver el fondo indicado por assetId: " + String(background_data.get("assetId", ""))
			return false
		var background_path := String(resolved_background.get("path", ""))
		if not background_path.is_empty():
			if not set_background(background_path):
				last_error = "No se pudo cargar el fondo: " + background_path
				return false
			background_sprite.set_meta(
				"jedl_asset_id",
				String(resolved_background.get("assetId", resolved_background.get("id", "")))
			)
	elif background_data is String and not background_data.is_empty():
		if not set_background(background_data):
			return false
	if not _instantiate_entries(scene_data["characters"], "3d"):
		if last_error.is_empty(): last_error = "No se pudieron crear los personajes. Revisa sus assetId y rutas."
		return false
	if not _instantiate_entries(scene_data["objects"], "3d"):
		if last_error.is_empty(): last_error = "No se pudieron crear los objetos. Revisa sus assetId y rutas."
		return false
	if candidate.has("elements"):
		if typeof(candidate["elements"]) != TYPE_ARRAY or not _instantiate_entries(candidate["elements"], "2d"):
			push_error("Scene JSON elements must be an array of scene resources")
			return false
	if not _build_timeline():
		return false
	return true


func _resolve_scene_entry(raw_entry: Dictionary, expected_kind: String = "3d") -> Dictionary:
	var entry := raw_entry.duplicate(true)
	var asset_id := String(entry.get("assetId", ""))
	if asset_id.is_empty():
		return entry
	if catalog_manager == null:
		last_missing_entry_id = String(entry.get("id", ""))
		last_missing_kind = String(entry.get("kind", expected_kind))
		last_missing_category = String(entry.get("category", ""))
		if last_missing_category.is_empty():
			last_missing_category = "Personajes 3D" if last_missing_kind == "3d" else "Elementos 2D"
		last_error = "No existe un catálogo disponible para resolver el recurso: " + asset_id
		push_error(last_error)
		return {}
	var resolved: Dictionary = catalog_manager.resolve_asset_id(asset_id)
	if resolved.is_empty():
		last_missing_entry_id = String(entry.get("id", ""))
		last_missing_kind = String(entry.get("kind", expected_kind))
		last_missing_category = String(entry.get("category", ""))
		if last_missing_category.is_empty():
			last_missing_category = "Personajes 3D" if last_missing_kind == "3d" else "Elementos 2D"
		last_error = "No existe en el inventario el assetId: " + asset_id
		push_error(last_error)
		return {}
	for key in ["path", "kind", "category", "license", "sha256"]:
		if resolved.has(key):
			entry[key] = resolved[key]
	return entry


func _instantiate_entries(entries: Array, expected_kind: String = "3d") -> bool:
	for entry_value in entries:
		if typeof(entry_value) != TYPE_DICTIONARY:
			push_error("Scene entry must be an object")
			return false
		var entry: Dictionary = _resolve_scene_entry(entry_value, expected_kind)
		if entry.is_empty():
			return false
		var resource_path := String(entry.get("path", ""))
		if resource_path.is_empty() or not ResourceLoader.exists(resource_path):
			last_missing_entry_id = String(entry.get("id", ""))
			last_missing_kind = String(entry.get("kind", expected_kind))
			last_missing_category = String(entry.get("category", ""))
			if last_missing_category.is_empty():
				last_missing_category = "Personajes 3D" if last_missing_kind == "3d" else "Elementos 2D"
			last_error = "El recurso local no existe o no está importado: " + resource_path
			push_error(last_error)
			return false
		var instance: Node
		var extension := resource_path.get_extension().to_lower()
		if extension in ["png", "jpg", "jpeg", "webp"]:
			var texture := load(resource_path) as Texture2D
			if texture == null:
				last_error = "No se pudo abrir la textura 2D: " + resource_path
				push_error(last_error)
				return false
			if expected_kind == "2d":
				if canvas_root == null:
					last_error = "El lienzo 2D independiente no está disponible."
					push_error(last_error)
					return false
				instance = _create_2d_canvas_element(texture, entry)
			else:
				instance = _create_2d_element(texture, entry)
		else:
			var packed := load(resource_path) as PackedScene
			if packed == null:
				last_error = "El modelo 3D no se importó como escena: " + resource_path
				push_error(last_error)
				return false
			var candidate := packed.instantiate()
			if not candidate is Node3D:
				candidate.queue_free()
				last_error = "El modelo debe tener una raíz Node3D: " + resource_path
				push_error(last_error)
				return false
			instance = candidate as Node3D
		instance.name = String(entry.get("name", entry.get("id", resource_path.get_file().get_basename())))
		var entry_id := String(entry.get("id", instance.name))
		instance.set_meta("jedl_entry_id", entry_id)
		instance.set_meta("jedl_asset_id", String(entry.get("assetId", entry.get("id", ""))))
		instance.set_meta("jedl_layer", String(entry.get("layer", "objects")))
		var position_value := _vector3_from(entry.get("position", [0.0, 0.0, 0.0]))
		if entry.has("depth"):
			position_value.z = float(entry["depth"])
		var rotation_value := _vector3_from(entry.get("rotation_degrees", [0.0, 0.0, 0.0]))
		var scale_value := _vector3_from(entry.get("scale", [1.0, 1.0, 1.0]))
		_apply_instance_transform(instance, position_value, rotation_value, scale_value)
		if instance is Node2D:
			canvas_root.add_child(instance)
		elif instance is Node3D and world_root != null:
			world_root.add_child(instance)
		else:
			instance.queue_free()
			last_error = "No existe un contenedor compatible para el recurso: " + resource_path
			return false
		active_instances.append(instance)
		if timeline_engine != null:
			timeline_engine.register_target(entry_id, instance)
		var animation_name := String(entry.get("animation", ""))
		if not animation_name.is_empty():
			var should_loop := bool(entry.get("animation_loop", true))
			_play_animation(instance, animation_name, should_loop)
	return true


func _create_2d_canvas_element(texture: Texture2D, entry: Dictionary = {}) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = true
	var position_value := _vector3_from(entry.get("position", [0.0, 0.0, 0.0]))
	var rotation_value := _vector3_from(entry.get("rotation_degrees", [0.0, 0.0, 0.0]))
	var scale_value := _vector3_from(entry.get("scale", [1.0, 1.0, 1.0]))
	sprite.position = Vector2(position_value.x * 100.0, -position_value.y * 100.0)
	sprite.rotation_degrees = rotation_value.z
	sprite.scale = Vector2(scale_value.x, scale_value.y)
	sprite.z_index = int(entry.get("z_index", 0))
	return sprite


func _apply_instance_transform(instance: Node, position_value: Vector3, rotation_value: Vector3, scale_value: Vector3) -> void:
	if instance is Node2D:
		var canvas_sprite := instance as Node2D
		canvas_sprite.position = Vector2(position_value.x * 100.0, -position_value.y * 100.0)
		canvas_sprite.rotation_degrees = rotation_value.z
		canvas_sprite.scale = Vector2(scale_value.x, scale_value.y)
	elif instance is Node3D:
		var stage_instance := instance as Node3D
		stage_instance.position = position_value
		stage_instance.rotation_degrees = rotation_value
		stage_instance.scale = scale_value


func _create_2d_element(texture: Texture2D, entry: Dictionary = {}) -> Sprite3D:
	var sprite := Sprite3D.new()
	sprite.texture = texture
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.pixel_size = maxf(0.0001, float(entry.get("pixel_size", 0.01)))
	sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_texture = texture
	sprite.material_override = material
	return sprite


func clear_background() -> void:
	if background_sprite != null and is_instance_valid(background_sprite):
		background_sprite.queue_free()
	background_sprite = null


func set_background(resource_path: String) -> bool:
	if camera == null or resource_path.is_empty():
		push_error("A camera and a valid background path are required")
		return false
	var texture := load(resource_path) as Texture2D
	if texture == null:
		push_error("Background texture could not be loaded: " + resource_path)
		return false
	clear_background()
	background_sprite = Sprite3D.new()
	background_sprite.name = "SceneBackground"
	background_sprite.texture = texture
	background_sprite.billboard = BaseMaterial3D.BILLBOARD_DISABLED
	background_sprite.pixel_size = 1.0
	background_sprite.position = Vector3(0.0, 0.0, -80.0)
	background_sprite.render_priority = -10
	background_sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.albedo_texture = texture
	background_sprite.material_override = material
	camera.add_child(background_sprite)
	camera.far = maxf(camera.far, 200.0)
	_fit_background_to_camera()
	return true


func _fit_background_to_camera() -> void:
	if camera == null or background_sprite == null or background_sprite.texture == null:
		return
	var distance := absf(background_sprite.position.z)
	var viewport_size := get_viewport().get_visible_rect().size
	var aspect := viewport_size.x / maxf(viewport_size.y, 1.0)
	var height := 2.0 * distance * tan(deg_to_rad(camera.fov) * 0.5)
	var width := height * aspect
	var texture_size := background_sprite.texture.get_size()
	var cover_scale := maxf(width / maxf(texture_size.x, 1.0), height / maxf(texture_size.y, 1.0))
	background_sprite.scale = Vector3(cover_scale, cover_scale, 1.0)


func add_catalog_asset(resource_path: String, as_background: bool = true, asset_id: String = "") -> bool:
	if resource_path.is_empty():
		return false

	var extension := resource_path.get_extension().to_lower()
	var instance: Node
	if extension in ["png", "jpg", "jpeg", "webp"]:
		if as_background:
			if not set_background(resource_path):
				return false
			background_sprite.set_meta("jedl_asset_id", asset_id)
			return true
		var texture := load(resource_path) as Texture2D
		if texture == null or canvas_root == null:
			return false
		instance = _create_2d_canvas_element(texture)
	elif extension in ["glb", "gltf", "tscn"]:
		var packed := load(resource_path) as PackedScene
		if packed == null:
			push_error("Catalog model is not an imported PackedScene: " + resource_path)
			return false
		var candidate := packed.instantiate()
		if not candidate is Node3D:
			candidate.queue_free()
			push_error("Catalog model root must be Node3D: " + resource_path)
			return false
		instance = candidate as Node3D
	else:
		push_error("Unsupported catalog asset type: " + resource_path)
		return false

	var placement_index := active_instances.size()
	var instance_id := "%s_%d" % [asset_id.replace(".", "_"), placement_index + 1]
	instance.set_meta("jedl_asset_id", asset_id)
	instance.set_meta("jedl_entry_id", instance_id)
	instance.set_meta("jedl_layer", "gallery")
	if instance is Node2D:
		(instance as Node2D).position = Vector2(float(placement_index) * 160.0, 0.0)
		canvas_root.add_child(instance)
	elif instance is Node3D and world_root != null:
		(instance as Node3D).position = Vector3(float(placement_index) * 1.6, 0.0, 0.0)
		world_root.add_child(instance)
	else:
		instance.queue_free()
		return false
	active_instances.append(instance)
	if timeline_engine != null:
		timeline_engine.register_target(instance_id, instance)
	if not scene_data.has("elements") or not (scene_data["elements"] is Array):
		scene_data["elements"] = []
	var asset_record: Dictionary = catalog_manager.resolve_asset_id(asset_id) if catalog_manager != null else {}
	scene_data["elements"].append({
		"id": instance_id,
		"assetId": asset_id,
		"kind": String(asset_record.get("kind", "2d" if extension in ["png", "jpg", "jpeg", "webp"] else "3d")),
		"category": String(asset_record.get("category", "")),
		"position": _instance_position_data(instance),
		"rotation_degrees": _instance_rotation_data(instance),
		"scale": _instance_scale_data(instance),
		"layer": "gallery"
	})
	_play_default_animation(instance)
	return true


func _instance_position_data(instance: Node) -> Array:
	if instance is Node2D:
		var canvas_instance := instance as Node2D
		return [canvas_instance.position.x / 100.0, -canvas_instance.position.y / 100.0, 0.0]
	if instance is Node3D:
		var stage_instance := instance as Node3D
		return [stage_instance.position.x, stage_instance.position.y, stage_instance.position.z]
	return [0.0, 0.0, 0.0]


func _instance_rotation_data(instance: Node) -> Array:
	if instance is Node2D:
		return [0.0, 0.0, (instance as Node2D).rotation_degrees]
	if instance is Node3D:
		var stage_instance := instance as Node3D
		return [stage_instance.rotation_degrees.x, stage_instance.rotation_degrees.y, stage_instance.rotation_degrees.z]
	return [0.0, 0.0, 0.0]


func _instance_scale_data(instance: Node) -> Array:
	if instance is Node2D:
		var canvas_instance := instance as Node2D
		return [canvas_instance.scale.x, canvas_instance.scale.y, 1.0]
	if instance is Node3D:
		var stage_instance := instance as Node3D
		return [stage_instance.scale.x, stage_instance.scale.y, stage_instance.scale.z]
	return [1.0, 1.0, 1.0]


func _play_default_animation(instance: Node) -> void:
	var players := instance.find_children("*", "AnimationPlayer", true, false)
	for candidate in players:
		var player := candidate as AnimationPlayer
		if player == null:
			continue
		var animations := player.get_animation_list()
		if animations.size() > 0:
			var default_animation := "Walk" if player.has_animation("Walk") else String(animations[0])
			_play_animation(instance, default_animation, true)
			return


func _vector3_from(value: Variant) -> Vector3:
	if typeof(value) == TYPE_ARRAY and value.size() >= 3:
		return Vector3(float(value[0]), float(value[1]), float(value[2]))
	return Vector3.ZERO


func _play_animation(instance: Node, animation_name: String, should_loop: bool = true) -> void:
	var players := instance.find_children("*", "AnimationPlayer", true, false)
	for candidate in players:
		var player := candidate as AnimationPlayer
		if player == null or not player.has_animation(animation_name):
			continue
		var animation := player.get_animation(animation_name)
		if animation != null:
			_configure_animation_loop(animation, should_loop)
		_active_animation_players.append({"player": player, "name": animation_name})
		player.play(animation_name)
		player.seek(0.0, true)
		return


func _configure_animation_loop(animation: Animation, should_loop: bool) -> void:
	if animation == null:
		return
	animation.loop_mode = Animation.LOOP_LINEAR if should_loop else Animation.LOOP_NONE


func _restart_animations() -> void:
	for item in _active_animation_players:
		var player := item.get("player") as AnimationPlayer
		var animation_name := String(item.get("name", ""))
		if is_instance_valid(player) and player.has_animation(animation_name):
			player.play(animation_name)
			player.seek(0.0, true)


func _stop_animations() -> void:
	for item in _active_animation_players:
		var player := item.get("player") as AnimationPlayer
		if is_instance_valid(player):
			player.stop()


func _build_timeline() -> bool:
	for subtitle_value in scene_data.get("subtitles", []):
		if typeof(subtitle_value) != TYPE_DICTIONARY:
			continue
		var subtitle: Dictionary = subtitle_value
		var start := maxf(0.0, float(subtitle.get("time", 0.0)))
		var duration := maxf(0.0, float(subtitle.get("duration", 0.0)))
		_events.append({"time": start, "kind": "subtitle", "text": String(subtitle.get("text", ""))})
		_events.append({"time": start + duration, "kind": "subtitle_clear", "text": ""})
	for sound_value in scene_data.get("sounds", []):
		if typeof(sound_value) != TYPE_DICTIONARY:
			continue
		var sound: Dictionary = sound_value
		_events.append({
			"time": maxf(0.0, float(sound.get("time", 0.0))),
			"kind": "sound",
			"path": String(sound.get("path", ""))
		})
	_events.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return float(a["time"]) < float(b["time"])
	)
	if timeline_engine != null:
		if not timeline_engine.compile_json_actions(scene_data.get("actions", [])):
			last_error = timeline_engine.last_error
			return false
	return true


func play_scene() -> void:
	_restart_animations()
	if timeline_engine != null:
		timeline_engine.play()
	_playback_time = 0.0
	_next_event = 0
	_playing = true
	if subtitle_label != null:
		subtitle_label.text = ""
	set_process(true)


func stop_scene() -> void:
	_playing = false
	set_process(false)
	_stop_animations()
	if timeline_engine != null:
		timeline_engine.stop()


func pause_scene() -> void:
	if timeline_engine != null:
		timeline_engine.pause()
	_playing = false
	set_process(false)


func resume_scene() -> void:
	if timeline_engine != null:
		timeline_engine.resume()
	_playing = true
	set_process(true)


func seek_scene(time_seconds: float) -> void:
	if timeline_engine != null:
		timeline_engine.seek(time_seconds)


func _process(delta: float) -> void:
	if not _playing:
		return
	_playback_time += delta
	while _next_event < _events.size() and float(_events[_next_event]["time"]) <= _playback_time:
		_dispatch_event(_events[_next_event])
		_next_event += 1
	if _next_event >= _events.size():
		_playing = false
		set_process(false)


func _dispatch_event(event: Dictionary) -> void:
	var kind := String(event.get("kind", ""))
	if kind == "subtitle" and subtitle_label != null:
		subtitle_label.set("text", String(event.get("text", "")))
	elif kind == "subtitle_clear" and subtitle_label != null:
		subtitle_label.set("text", "")
	elif kind == "sound" and audio_player != null:
		var sound_path := String(event.get("path", ""))
		if not sound_path.is_empty():
			var stream := load(sound_path) as AudioStream
			if stream != null:
				audio_player.stream = stream
				audio_player.play()


func _clear_instances() -> void:
	for instance in active_instances:
		if is_instance_valid(instance):
			instance.queue_free()
	active_instances.clear()
	_active_animation_players.clear()
	if timeline_engine != null:
		timeline_engine.clear_targets()
		timeline_engine.clear_timeline()
