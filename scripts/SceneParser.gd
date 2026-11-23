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
var _action_tracks: Array[Dictionary] = []
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
    _clear_instances()
    scene_data = candidate
    _events.clear()
    _playing = false
    _playback_time = 0.0
    _next_event = 0
    if not _instantiate_entries(scene_data["characters"]):
        if last_error.is_empty(): last_error = "No se pudieron crear los personajes. Revisa sus assetId y rutas."
        return false
    if not _instantiate_entries(scene_data["objects"]):
        if last_error.is_empty(): last_error = "No se pudieron crear los objetos. Revisa sus assetId y rutas."
        return false
    if candidate.has("elements"):
        if typeof(candidate["elements"]) != TYPE_ARRAY or not _instantiate_entries(candidate["elements"]):
            push_error("Scene JSON elements must be an array of scene resources")
            return false
    if candidate.has("actions") and typeof(candidate["actions"]) != TYPE_ARRAY:
        last_error = "El campo actions debe ser una lista []."
        push_error(last_error)
        return false
    if not _build_timeline():
        return false
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
    _action_tracks.clear()
    for action_value in scene_data.get("actions", []):
        if typeof(action_value) != TYPE_DICTIONARY:
            last_error = "Cada acción debe ser un objeto JSON."
            push_error(last_error)
            return false
        var action: Dictionary = action_value
        var target_id := String(action.get("target", ""))
        var property := String(action.get("property", ""))
        if target_id.is_empty() or property not in ["position", "rotation_degrees", "scale"]:
            last_error = "Acción inválida: target y property válidos son obligatorios."
            push_error(last_error)
            return false
        var target_node: Node3D
        for instance in active_instances:
            if String(instance.get_meta("jedl_entry_id", "")) == target_id or String(instance.get_meta("jedl_asset_id", "")) == target_id or instance.name == target_id:
                target_node = instance
                break
        if target_node == null:
            last_error = "La acción referencia un elemento inexistente: " + target_id
            push_error(last_error)
            return false
        var start_time := float(action.get("time", 0.0))
        var duration := float(action.get("duration", 0.0))
        var destination_value: Variant = action.get("to", null)
        if start_time < 0.0 or duration <= 0.0 or typeof(destination_value) != TYPE_ARRAY or destination_value.size() != 3:
            last_error = "Acción inválida: time >= 0, duration > 0 y to=[x,y,z] son obligatorios."
            push_error(last_error)
            return false
        var origin := _get_transform_vector(target_node, property)
        var destination := _vector3_from(destination_value)
        if property == "scale" and (destination.x == 0.0 or destination.y == 0.0 or destination.z == 0.0):
            last_error = "Una acción no puede establecer escala cero."
            push_error(last_error)
            return false
        _action_tracks.append({"target": target_node, "property": property, "start": start_time, "duration": duration, "from": origin, "to": destination})
        _events.append({"time": start_time + duration, "kind": "action_end"})
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
    return true


func play_scene() -> void:
    _restart_animations()
    _playback_time = 0.0
    _next_event = 0
    for track in _action_tracks:
        var target := track["target"] as Node3D
        if is_instance_valid(target):
            _set_transform_vector(target, String(track["property"]), track["from"])
    _playing = true
    if subtitle_label != null:
        subtitle_label.text = ""
    set_process(true)


func stop_scene() -> void:
    _playing = false
    set_process(false)
    _stop_animations()


func _process(delta: float) -> void:
    if not _playing:
        return
    _playback_time += delta
    _update_action_tracks()
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

func _get_transform_vector(target: Node3D, property: String) -> Vector3:
    if property == "position":
        return target.position
    if property == "rotation_degrees":
        return target.rotation_degrees
    return target.scale


func _set_transform_vector(target: Node3D, property: String, value: Vector3) -> void:
    if property == "position":
        target.position = value
    elif property == "rotation_degrees":
        target.rotation_degrees = value
    elif property == "scale":
        target.scale = value


func _update_action_tracks() -> void:
    for track in _action_tracks:
        var target := track["target"] as Node3D
        if not is_instance_valid(target):
            continue
        var elapsed := _playback_time - float(track["start"])
        if elapsed < 0.0:
            continue
        var weight := clampf(elapsed / float(track["duration"]), 0.0, 1.0)
        var origin: Vector3 = track["from"]
        var destination: Vector3 = track["to"]
        _set_transform_vector(target, String(track["property"]), origin.lerp(destination, weight))

func _clear_instances() -> void:
    for instance in active_instances:
        if is_instance_valid(instance):
            instance.queue_free()
    active_instances.clear()
    _active_animation_players.clear()
    _action_tracks.clear()
