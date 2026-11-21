extends Node
class_name SceneParser

var world_root: Node3D
var subtitle_label: Control
var audio_player: AudioStreamPlayer
var scene_data: Dictionary = {}
var active_instances: Array[Node3D] = []
var _events: Array[Dictionary] = []
var _playing := false
var _playback_time := 0.0
var _next_event := 0
var _active_animation_players: Array[Dictionary] = []


func load_scene_file(path: String) -> bool:
    if not FileAccess.file_exists(path):
        push_error("Scene JSON not found: " + path)
        return false
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        push_error("Cannot open scene JSON: " + path)
        return false
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("Scene JSON root must be an object")
        return false
    var candidate: Dictionary = parsed
    for key in ["characters", "objects", "subtitles", "sounds"]:
        if not candidate.has(key) or typeof(candidate[key]) != TYPE_ARRAY:
            push_error("Scene JSON requires array: " + key)
            return false
    _clear_instances()
    scene_data = candidate
    _events.clear()
    _playing = false
    _playback_time = 0.0
    _next_event = 0
    if not _instantiate_entries(scene_data["characters"]):
        return false
    if not _instantiate_entries(scene_data["objects"]):
        return false
    _build_timeline()
    return true


func _instantiate_entries(entries: Array) -> bool:
    for entry_value in entries:
        if typeof(entry_value) != TYPE_DICTIONARY:
            push_error("Scene entry must be an object")
            return false
        var entry: Dictionary = entry_value
        var resource_path := String(entry.get("path", ""))
        if resource_path.is_empty():
            push_error("Scene entry is missing path")
            return false
        var packed := load(resource_path) as PackedScene
        if packed == null:
            push_error("Scene resource is not an imported PackedScene: " + resource_path)
            return false
        var instance := packed.instantiate()
        if not instance is Node3D:
            instance.queue_free()
            push_error("Scene resource root must be Node3D: " + resource_path)
            return false
        var node := instance as Node3D
        node.position = _vector3_from(entry.get("position", [0.0, 0.0, 0.0]))
        node.rotation_degrees = _vector3_from(entry.get("rotation_degrees", [0.0, 0.0, 0.0]))
        node.scale = _vector3_from(entry.get("scale", [1.0, 1.0, 1.0]))
        if world_root != null:
            world_root.add_child(node)
        active_instances.append(node)
        var animation_name := String(entry.get("animation", ""))
        if not animation_name.is_empty():
            var should_loop := bool(entry.get("animation_loop", true))
            _play_animation(node, animation_name, should_loop)
    return true


func add_catalog_asset(resource_path: String) -> bool:
    if world_root == null or resource_path.is_empty():
        return false

    var extension := resource_path.get_extension().to_lower()
    var instance: Node3D
    if extension in ["png", "jpg", "jpeg", "webp"]:
        var texture := load(resource_path) as Texture2D
        if texture == null:
            push_error("Catalog image could not be loaded: " + resource_path)
            return false
        var sprite := Sprite3D.new()
        sprite.texture = texture
        sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
        var largest_dimension := maxf(float(texture.get_width()), float(texture.get_height()))
        sprite.pixel_size = 1.2 / maxf(largest_dimension, 1.0)
        instance = sprite
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
    instance.position = Vector3(float((placement_index % 3) - 1) * 1.6, 0.0, 0.0)
    world_root.add_child(instance)
    active_instances.append(instance)
    return true


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


func _build_timeline() -> void:
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


func play_scene() -> void:
    _restart_animations()
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
