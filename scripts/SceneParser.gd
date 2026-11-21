extends Node
class_name SceneParser

var world_root: Node3D
var subtitle_label: RichTextLabel
var audio_player: AudioStreamPlayer

var scene_data: Dictionary = {}
var active_instances: Array = []
var _events: Array[Dictionary] = []
var _playing: bool = false
var _elapsed: float = 0.0
var _next_event: int = 0


func load_scene_file(file_path: String) -> bool:
    if not FileAccess.file_exists(file_path):
        push_error("Scene JSON not found: " + file_path)
        return false

    var file := FileAccess.open(file_path, FileAccess.READ)
    if file == null:
        push_error("Unable to open scene JSON: " + file_path)
        return false

    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if not (parsed is Dictionary):
        push_error("Scene JSON root must be an object")
        return false

    for key in ["characters", "objects", "subtitles", "sounds"]:
        if not parsed.has(key) or not (parsed[key] is Array):
            push_error("Scene JSON requires array: " + key)
            return false

    scene_data = parsed
    _stop_playback()
    _clear_instances()
    _events.clear()

    if not _instantiate_entries(scene_data["characters"], "characters"):
        return false
    if not _instantiate_entries(scene_data["objects"], "objects"):
        return false

    _build_timeline(scene_data["subtitles"], scene_data["sounds"])
    return true


func _instantiate_entries(entries: Array, category: String) -> bool:
    if world_root == null:
        push_error("SceneParser.world_root is not assigned")
        return false

    for entry_variant in entries:
        if not (entry_variant is Dictionary):
            push_error("Every " + category + " entry must be an object")
            return false
        var entry: Dictionary = entry_variant
        var asset_path := String(entry.get("path", ""))
        var allowed_root := "res://assets/" + category + "/"
        if not asset_path.begins_with(allowed_root):
            push_error("Asset path is outside " + allowed_root + ": " + asset_path)
            return false
        if not ResourceLoader.exists(asset_path):
            push_error("Asset does not exist: " + asset_path)
            return false

        var packed := ResourceLoader.load(asset_path) as PackedScene
        if packed == null:
            push_error("Asset is not an instantiable scene: " + asset_path)
            return false
        var instance := packed.instantiate()
        if instance == null:
            push_error("Unable to instantiate asset: " + asset_path)
            return false

        world_root.add_child(instance)
        if instance is Node3D:
            var spatial := instance as Node3D
            spatial.position = _vector3_from(entry.get("position", [0.0, 0.0, 0.0]))
            spatial.rotation_degrees = _vector3_from(entry.get("rotation_degrees", [0.0, 0.0, 0.0]))
            spatial.scale = _vector3_from(entry.get("scale", [1.0, 1.0, 1.0]))
        active_instances.append(instance)

        var animation_name := String(entry.get("animation", ""))
        if animation_name != "":
            var animation_player := _find_animation_player(instance)
            if animation_player != null and animation_player.has_animation(animation_name):
                animation_player.play(animation_name)
            elif animation_player != null:
                push_warning("Animation not found: " + animation_name)
    return true


func _find_animation_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node as AnimationPlayer
    for child in node.get_children():
        var found := _find_animation_player(child)
        if found != null:
            return found
    return null


func _vector3_from(value: Variant) -> Vector3:
    if value is Array and value.size() >= 3:
        return Vector3(float(value[0]), float(value[1]), float(value[2]))
    return Vector3.ZERO


func _build_timeline(subtitles: Array, sounds: Array) -> void:
    for subtitle_variant in subtitles:
        if not (subtitle_variant is Dictionary):
            continue
        var subtitle: Dictionary = subtitle_variant
        var start_time := maxf(0.0, float(subtitle.get("time", 0.0)))
        var duration := maxf(0.0, float(subtitle.get("duration", 0.0)))
        _events.append({
            "time": start_time,
            "kind": "subtitle",
            "text": String(subtitle.get("text", ""))
        })
        _events.append({
            "time": start_time + duration,
            "kind": "subtitle_clear",
            "text": ""
        })

    for sound_variant in sounds:
        if not (sound_variant is Dictionary):
            continue
        var sound: Dictionary = sound_variant
        _events.append({
            "time": maxf(0.0, float(sound.get("time", 0.0))),
            "kind": "sound",
            "path": String(sound.get("path", ""))
        })

    _events.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return float(a["time"]) < float(b["time"])
    )


func play_scene() -> void:
    _elapsed = 0.0
    _next_event = 0
    _playing = true
    if subtitle_label != null:
        subtitle_label.text = ""
    _process_timeline_events()


func _process(delta: float) -> void:
    if not _playing:
        return
    _elapsed += delta
    _process_timeline_events()
    if _next_event >= _events.size():
        _playing = false


func _process_timeline_events() -> void:
    while _next_event < _events.size():
        var event: Dictionary = _events[_next_event]
        if float(event["time"]) > _elapsed:
            break
        match String(event["kind"]):
            "subtitle":
                if subtitle_label != null:
                    subtitle_label.text = String(event.get("text", ""))
            "subtitle_clear":
                if subtitle_label != null:
                    subtitle_label.text = ""
            "sound":
                _play_sound(String(event.get("path", "")))
        _next_event += 1


func _play_sound(asset_path: String) -> void:
    if audio_player == null or asset_path == "":
        return
    if not asset_path.begins_with("res://assets/audio/"):
        push_warning("Sound path is outside res://assets/audio/: " + asset_path)
        return
    if not ResourceLoader.exists(asset_path):
        push_warning("Sound asset not found: " + asset_path)
        return
    var stream := ResourceLoader.load(asset_path) as AudioStream
    if stream != null:
        audio_player.stream = stream
        audio_player.play()


func _clear_instances() -> void:
    for instance in active_instances:
        if is_instance_valid(instance):
            instance.queue_free()
    active_instances.clear()


func _stop_playback() -> void:
    _playing = false
    _elapsed = 0.0
    _next_event = 0
