extends Node
class_name SceneParser

var world_root: Node3D
var camera: Camera3D
var subtitle_label: Control
var audio_player: AudioStreamPlayer
var catalog_manager: Node
var scene_data: Dictionary = {}
var active_instances: Array[Node3D] = []
var _events: Array[Dictionary] = []
var _playing := false
var _playback_time := 0.0
var _next_event := 0
var _active_animation_players: Array[Dictionary] = []
var _timeline_player: AnimationPlayer
var _timeline_animation_name := "JSONActions"
var _timeline_length := 0.0
var _playback_paused := false
var _loop_playback := false
var last_error := ""


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
    if candidate.has("elements") and typeof(candidate["elements"]) != TYPE_ARRAY:
        last_error = "El campo elements debe ser una lista []."
        push_error(last_error)
        return false
    if candidate.has("actions") and typeof(candidate["actions"]) != TYPE_ARRAY:
        last_error = "El campo actions debe ser una lista []."
        push_error(last_error)
        return false
    if world_root == null:
        last_error = "No existe un contenedor de escena activo."
        push_error(last_error)
        return false

    var previous_scene_data := scene_data
    var previous_instances := active_instances.duplicate()
    var previous_events := _events.duplicate(true)
    var previous_animation_players := _active_animation_players.duplicate()
    var previous_timeline_player := _timeline_player
    var previous_timeline_length := _timeline_length
    var previous_playback_time := _playback_time
    var previous_next_event := _next_event
    var previous_playing := _playing
    var previous_paused := _playback_paused
    var committed_root: Node3D = world_root
    var staging_root := Node3D.new()
    staging_root.name = "JEDLSceneCandidate"
    committed_root.add_child(staging_root)

    scene_data = candidate.duplicate(true)
    active_instances = []
    _events = []
    _active_animation_players = []
    _timeline_player = null
    _timeline_length = 0.0
    _playback_time = 0.0
    _next_event = 0
    _playing = false
    _playback_paused = false
    world_root = staging_root

    var valid := _instantiate_entries(scene_data["characters"])
    if valid:
        valid = _instantiate_entries(scene_data["objects"])
    if valid and scene_data.has("elements"):
        valid = _instantiate_entries(scene_data["elements"])
    if valid:
        valid = _build_timeline()

    if not valid:
        if last_error.is_empty():
            last_error = "No se pudo construir la escena candidata."
        staging_root.queue_free()
        world_root = committed_root
        scene_data = previous_scene_data
        active_instances = previous_instances
        _events = previous_events
        _active_animation_players = previous_animation_players
        _timeline_player = previous_timeline_player
        _timeline_length = previous_timeline_length
        _playback_time = previous_playback_time
        _next_event = previous_next_event
        _playing = previous_playing
        _playback_paused = previous_paused
        return false

    for child in staging_root.get_children():
        staging_root.remove_child(child)
        committed_root.add_child(child)
    staging_root.queue_free()
    world_root = committed_root

    for old_instance in previous_instances:
        if is_instance_valid(old_instance):
            old_instance.queue_free()
    if is_instance_valid(previous_timeline_player):
        previous_timeline_player.queue_free()
    _playing = false
    _playback_paused = false
    _playback_time = 0.0
    _next_event = 0
    if subtitle_label != null:
        subtitle_label.text = ""
    if audio_player != null:
        audio_player.stop()
    return true

func _resolve_scene_entry(raw_entry: Dictionary) -> Dictionary:
    var entry := raw_entry.duplicate(true)
    var asset_id := String(entry.get("assetId", ""))
    if asset_id.is_empty():
        return entry
    if catalog_manager == null:
        push_error("Scene entry requires CatalogManager for assetId: " + asset_id)
        return {}
    var resolved: Dictionary = catalog_manager.resolve_asset_id(asset_id)
    if resolved.is_empty():
        last_error = "No existe en el inventario el assetId: " + asset_id
        push_error(last_error)
        return {}
    for key in ["path", "kind", "category", "license", "sha256"]:
        if resolved.has(key):
            entry[key] = resolved[key]
    return entry


func _instantiate_entries(entries: Array) -> bool:
    for entry_value in entries:
        if typeof(entry_value) != TYPE_DICTIONARY:
            push_error("Scene entry must be an object")
            return false
        var entry: Dictionary = _resolve_scene_entry(entry_value)
        if entry.is_empty():
            return false
        var resource_path := String(entry.get("path", ""))
        if resource_path.is_empty():
            last_error = "Elemento '%s' sin ruta ni assetId válido." % String(entry.get("id", "desconocido"))
            push_error(last_error)
            return false
        var instance: Node3D
        var extension := resource_path.get_extension().to_lower()
        if extension in ["png", "jpg", "jpeg", "webp"]:
            var texture := load(resource_path) as Texture2D
            if texture == null:
                last_error = "No se pudo abrir la textura 2D: " + resource_path
                push_error(last_error)
                return false
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
        instance.set_meta("jedl_asset_id", String(entry.get("assetId", entry.get("id", ""))))
        instance.set_meta("jedl_entry_id", String(entry.get("id", "")))
        instance.set_meta("jedl_layer", String(entry.get("layer", "objects")))
        instance.position = _vector3_from(entry.get("position", [0.0, 0.0, 0.0]))
        if entry.has("depth"):
            instance.position.z = float(entry["depth"])
        instance.rotation_degrees = _vector3_from(entry.get("rotation_degrees", [0.0, 0.0, 0.0]))
        instance.scale = _vector3_from(entry.get("scale", [1.0, 1.0, 1.0]))
        if world_root != null:
            world_root.add_child(instance)
        active_instances.append(instance)
        var animation_name := String(entry.get("animation", ""))
        if not animation_name.is_empty():
            var should_loop := bool(entry.get("animation_loop", true))
            _play_animation(instance, animation_name, should_loop)
    return true


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


func add_catalog_asset(resource_path: String, asset_id: String = "") -> bool:
    if world_root == null or resource_path.is_empty():
        return false

    var extension := resource_path.get_extension().to_lower()
    var instance: Node3D
    if extension in ["png", "jpg", "jpeg", "webp"]:
        var texture := load(resource_path) as Texture2D
        if texture == null:
            return false
        instance = _create_2d_element(texture)
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
    instance.position = Vector3(float(placement_index) * 1.6, 0.0, 0.0)
    instance.set_meta("jedl_asset_id", asset_id)
    world_root.add_child(instance)
    active_instances.append(instance)
    _play_default_animation(instance)
    return true


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
    _events.clear()
    _timeline_length = 0.0
    var tracks_by_key: Dictionary = {}
    var action_groups: Dictionary = {}

    for action_value in scene_data.get("actions", []):
        if typeof(action_value) != TYPE_DICTIONARY:
            last_error = "Cada acción debe ser un objeto JSON."
            push_error(last_error)
            return false
        var action: Dictionary = action_value
        var target_id := String(action.get("target", "")).strip_edges()
        var property := String(action.get("property", ""))
        if target_id.is_empty() or property not in ["position", "rotation_degrees", "scale"]:
            last_error = "Acción inválida: target y property válidos son obligatorios."
            push_error(last_error)
            return false
        if not action.has("time") or not action.has("duration") or not action.has("to"):
            last_error = "Cada acción requiere time, duration y to."
            push_error(last_error)
            return false
        if typeof(action["time"]) not in [TYPE_INT, TYPE_FLOAT] or typeof(action["duration"]) not in [TYPE_INT, TYPE_FLOAT]:
            last_error = "time y duration deben ser valores numéricos."
            push_error(last_error)
            return false
        var start_time := float(action["time"])
        var duration := float(action["duration"])
        var destination_value: Variant = action["to"]
        if not is_finite(start_time) or not is_finite(duration) or start_time < 0.0 or duration <= 0.0:
            last_error = "Acción inválida: time debe ser >= 0 y duration > 0."
            push_error(last_error)
            return false
        if typeof(destination_value) != TYPE_ARRAY or destination_value.size() != 3:
            last_error = "to debe contener exactamente tres componentes numéricos."
            push_error(last_error)
            return false
        for component in destination_value:
            if typeof(component) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(component)):
                last_error = "Los componentes de to deben ser números finitos."
                push_error(last_error)
                return false

        var target_result := _resolve_action_target(target_id)
        if not target_result.get("ok", false):
            last_error = String(target_result.get("error", "No se pudo resolver el objetivo de la acción."))
            push_error(last_error)
            return false
        var target_node := target_result["node"] as Node3D
        var destination := _vector3_from(destination_value)
        if property == "scale" and (is_zero_approx(destination.x) or is_zero_approx(destination.y) or is_zero_approx(destination.z)):
            last_error = "Una acción no puede establecer escala cero."
            push_error(last_error)
            return false

        var key := "%d:%s" % [target_node.get_instance_id(), property]
        if not action_groups.has(key):
            action_groups[key] = {"target": target_node, "property": property, "actions": []}
        action_groups[key]["actions"].append({
            "start": start_time,
            "end": start_time + duration,
            "duration": duration,
            "to": destination
        })
        _timeline_length = maxf(_timeline_length, start_time + duration)

    for key in action_groups:
        var group: Dictionary = action_groups[key]
        var actions: Array = group["actions"]
        actions.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
            if is_equal_approx(float(a["start"]), float(b["start"])):
                return float(a["end"]) < float(b["end"])
            return float(a["start"]) < float(b["start"])
        )
        var previous_end := -1.0
        for action in actions:
            var start_time := float(action["start"])
            var end_time := float(action["end"])
            if previous_end >= 0.0 and start_time < previous_end - 0.000001:
                last_error = "Hay acciones solapadas sobre la misma propiedad del mismo elemento."
                push_error(last_error)
                return false
            previous_end = end_time

    for subtitle_value in scene_data.get("subtitles", []):
        if typeof(subtitle_value) != TYPE_DICTIONARY:
            last_error = "Cada subtítulo debe ser un objeto JSON."
            push_error(last_error)
            return false
        var subtitle: Dictionary = subtitle_value
        var subtitle_time := _read_nonnegative_time(subtitle, "time", "subtítulo")
        var subtitle_duration := _read_nonnegative_time(subtitle, "duration", "subtítulo")
        if subtitle_time < 0.0 or subtitle_duration < 0.0:
            return false
        _events.append({"time": subtitle_time, "kind": "subtitle", "text": String(subtitle.get("text", ""))})
        _events.append({"time": subtitle_time + subtitle_duration, "kind": "subtitle_clear", "text": ""})
        _timeline_length = maxf(_timeline_length, subtitle_time + subtitle_duration)

    for sound_value in scene_data.get("sounds", []):
        if typeof(sound_value) != TYPE_DICTIONARY:
            last_error = "Cada sonido debe ser un objeto JSON."
            push_error(last_error)
            return false
        var sound: Dictionary = sound_value
        var sound_time := _read_nonnegative_time(sound, "time", "sonido")
        if sound_time < 0.0:
            return false
        var sound_path := String(sound.get("path", ""))
        if not sound_path.is_empty() and not ResourceLoader.exists(sound_path):
            last_error = "No existe el recurso de audio: " + sound_path
            push_error(last_error)
            return false
        _events.append({"time": sound_time, "kind": "sound", "path": sound_path})
        _timeline_length = maxf(_timeline_length, sound_time)

    _events.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return float(a["time"]) < float(b["time"])
    )

    if not action_groups.is_empty():
        _timeline_player = AnimationPlayer.new()
        _timeline_player.name = "JEDLTimelinePlayer"
        _timeline_player.root_node = NodePath("..")
        world_root.add_child(_timeline_player)
        var animation := Animation.new()
        animation.resource_name = _timeline_animation_name
        animation.length = maxf(_timeline_length, 0.001)
        for key in action_groups:
            var group: Dictionary = action_groups[key]
            var target := group["target"] as Node3D
            var property := String(group["property"])
            var track_index := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(track_index, NodePath("%s:%s" % [target.name, property]))
            animation.track_set_interpolation_type(track_index, Animation.INTERPOLATION_LINEAR)
            animation.value_track_set_update_mode(track_index, Animation.UPDATE_CONTINUOUS)
            var current_value := _get_transform_vector(target, property)
            animation.track_insert_key(track_index, 0.0, current_value)
            var actions: Array = group["actions"]
            actions.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
                return float(a["start"]) < float(b["start"])
            )
            var previous_end := -1.0
            for action in actions:
                var start_time := float(action["start"])
                var end_time := float(action["end"])
                var destination: Vector3 = action["to"]
                if start_time > 0.000001 and (previous_end < 0.0 or start_time > previous_end + 0.000001):
                    var held_value := current_value
                    animation.track_insert_key(track_index, start_time, held_value)
                animation.track_insert_key(track_index, end_time, destination)
                current_value = destination
                previous_end = end_time
        var add_error := _timeline_player.add_animation(_timeline_animation_name, animation)
        if add_error != OK:
            last_error = "No se pudo registrar la animación compilada en AnimationPlayer."
            push_error(last_error)
            return false
    return true


func _resolve_action_target(target_id: String) -> Dictionary:
    var exact_matches: Array[Node3D] = []
    var fallback_matches: Array[Node3D] = []
    for instance in active_instances:
        if not is_instance_valid(instance):
            continue
        if String(instance.get_meta("jedl_entry_id", "")) == target_id:
            exact_matches.append(instance)
        elif String(instance.get_meta("jedl_asset_id", "")) == target_id or instance.name == target_id:
            fallback_matches.append(instance)
    if exact_matches.size() == 1:
        return {"ok": true, "node": exact_matches[0]}
    if exact_matches.size() > 1:
        return {"ok": false, "error": "El target coincide con varios id de entrada: " + target_id}
    if fallback_matches.size() == 1:
        return {"ok": true, "node": fallback_matches[0]}
    if fallback_matches.size() > 1:
        return {"ok": false, "error": "El target es ambiguo; usa el id único de entrada: " + target_id}
    return {"ok": false, "error": "La acción referencia un elemento inexistente: " + target_id}


func _read_nonnegative_time(data: Dictionary, field: String, context: String) -> float:
    if not data.has(field):
        last_error = "Falta el campo %s en %s." % [field, context]
        push_error(last_error)
        return -1.0
    if typeof(data[field]) not in [TYPE_INT, TYPE_FLOAT]:
        last_error = "%s debe ser numérico en %s." % [field, context]
        push_error(last_error)
        return -1.0
    var value := float(data[field])
    if not is_finite(value) or value < 0.0:
        last_error = "%s debe ser un número finito no negativo en %s." % [field, context]
        push_error(last_error)
        return -1.0
    return value


func play_scene() -> void:
    if _timeline_player != null and _timeline_player.has_animation(_timeline_animation_name):
        _timeline_player.play(_timeline_animation_name)
        _timeline_player.pause()
    _restart_animations()
    _playing = true
    _playback_paused = false
    seek_scene(0.0)
    if subtitle_label != null:
        subtitle_label.text = ""
    set_process(true)


func pause_scene() -> void:
    if not _playing or _playback_paused:
        return
    _playback_paused = true
    if _timeline_player != null:
        _timeline_player.pause()


func resume_scene() -> void:
    if not _playing or not _playback_paused:
        return
    _playback_paused = false
    set_process(true)


func set_loop_playback(enabled: bool) -> void:
    _loop_playback = enabled


func seek_scene(time_seconds: float) -> void:
    _playback_time = clampf(time_seconds, 0.0, _timeline_length)
    if _timeline_player != null and _timeline_player.has_animation(_timeline_animation_name):
        if not _timeline_player.is_playing():
            _timeline_player.play(_timeline_animation_name)
            _timeline_player.pause()
        _timeline_player.seek(_playback_time, true)
    _next_event = 0
    while _next_event < _events.size() and float(_events[_next_event]["time"]) <= _playback_time:
        _next_event += 1
    if subtitle_label != null:
        subtitle_label.text = ""
        for subtitle_value in scene_data.get("subtitles", []):
            if typeof(subtitle_value) != TYPE_DICTIONARY:
                continue
            var subtitle: Dictionary = subtitle_value
            var start := float(subtitle.get("time", 0.0))
            var end := start + float(subtitle.get("duration", 0.0))
            if _playback_time >= start and _playback_time < end:
                subtitle_label.text = String(subtitle.get("text", ""))


func stop_scene() -> void:
    _playing = false
    _playback_paused = false
    set_process(false)
    if _timeline_player != null:
        _timeline_player.stop()
        _timeline_player.seek(0.0, true)
    _stop_animations()
    _playback_time = 0.0
    _next_event = 0
    if subtitle_label != null:
        subtitle_label.text = ""
    if audio_player != null:
        audio_player.stop()


func _process(delta: float) -> void:
    if not _playing or _playback_paused:
        return
    _playback_time = minf(_playback_time + delta, _timeline_length)
    if _timeline_player != null and _timeline_player.has_animation(_timeline_animation_name):
        _timeline_player.seek(_playback_time, true)
    while _next_event < _events.size() and float(_events[_next_event]["time"]) <= _playback_time:
        _dispatch_event(_events[_next_event])
        _next_event += 1
    if _playback_time >= _timeline_length:
        if _loop_playback and _timeline_length > 0.0:
            seek_scene(0.0)
        else:
            _playing = false
            _playback_paused = false
            if _timeline_player != null:
                _timeline_player.pause()
            set_process(false)


func _dispatch_event(event: Dictionary) -> void:
    var kind := String(event.get("kind", ""))
    if kind == "subtitle" and subtitle_label != null:
        subtitle_label.text = String(event.get("text", ""))
    elif kind == "subtitle_clear" and subtitle_label != null:
        subtitle_label.text = ""
    elif kind == "sound" and audio_player != null:
        var sound_path := String(event.get("path", ""))
        if not sound_path.is_empty():
            var stream := load(sound_path) as AudioStream
            if stream != null:
                audio_player.stream = stream
                audio_player.play()


func _get_transform_vector(target: Node3D, property: String) -> Vector3:
    if property == "position":
        return target.position
    if property == "rotation_degrees":
        return target.rotation_degrees
    return target.scale


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

func _clear_instances() -> void:
    for instance in active_instances:
        if is_instance_valid(instance):
            instance.queue_free()
    active_instances.clear()
    _active_animation_players.clear()
    if is_instance_valid(_timeline_player):
        _timeline_player.queue_free()
    _timeline_player = null
    _events.clear()
    _timeline_length = 0.0
    _playing = false
    _playback_paused = false
