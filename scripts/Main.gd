extends Node3D

const SceneParserScript = preload("res://scripts/SceneParser.gd")

var scene_parser: Node
var world_root: Node3D
var camera: Camera3D
var subtitle_label: Label
var audio_player: AudioStreamPlayer


func _ready() -> void:
    # Solicita orientación automática vertical y horizontal al iniciar.
    DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR)
    world_root = get_node_or_null("World") as Node3D
    if world_root == null:
        world_root = self
    camera = get_node_or_null("World/Camera3D") as Camera3D
    _build_overlay()
    scene_parser = SceneParserScript.new()
    add_child(scene_parser)
    scene_parser.world_root = world_root
    scene_parser.subtitle_label = subtitle_label
    scene_parser.audio_player = audio_player


func _build_overlay() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var panel := PanelContainer.new()
    panel.position = Vector2(16, 16)
    panel.custom_minimum_size = Vector2(300, 0)
    layer.add_child(panel)
    var column := VBoxContainer.new()
    panel.add_child(column)
    var heading := Label.new()
    heading.text = "JEDL Studio"
    column.add_child(heading)
    subtitle_label = Label.new()
    subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    column.add_child(subtitle_label)
    var row := HBoxContainer.new()
    column.add_child(row)
    var load_button := Button.new()
    load_button.text = "Cargar escena JSON"
    load_button.pressed.connect(_load_example_scene)
    row.add_child(load_button)
    var play_button := Button.new()
    play_button.text = "Reproducir"
    play_button.pressed.connect(_play_scene)
    row.add_child(play_button)
    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)


func _load_example_scene() -> void:
    if scene_parser != null and scene_parser.load_scene_file("res://scenes/scene.example.json"):
        _frame_camera_to_content()


func _calculate_camera_distance(bounds_size: Vector3, aspect_ratio: float, fov_degrees: float) -> float:
    var safe_aspect := maxf(aspect_ratio, 0.1)
    var safe_fov := clampf(fov_degrees, 10.0, 100.0)
    var vertical_fov := deg_to_rad(safe_fov)
    var required_height := maxf(bounds_size.y, bounds_size.x / safe_aspect)
    return (required_height / (2.0 * tan(vertical_fov * 0.5))) * 1.35 + bounds_size.z * 0.5


func _frame_camera_to_content() -> void:
    if camera == null or scene_parser == null:
        return

    var combined_bounds := AABB()
    var has_bounds := false
    for instance in scene_parser.active_instances:
        var visuals: Array[Node] = []
        if instance is VisualInstance3D:
            visuals.append(instance)
        visuals.append_array(instance.find_children("*", "VisualInstance3D", true, false))
        for visual_node in visuals:
            var visual := visual_node as VisualInstance3D
            if visual == null:
                continue
            var visual_bounds := visual.global_transform * visual.get_aabb()
            if visual_bounds.size.length() <= 0.001:
                continue
            if has_bounds:
                combined_bounds = combined_bounds.merge(visual_bounds)
            else:
                combined_bounds = visual_bounds
                has_bounds = true

    if not has_bounds:
        return

    var viewport_size := get_viewport().get_visible_rect().size
    var aspect_ratio := viewport_size.x / maxf(viewport_size.y, 1.0)
    var distance := _calculate_camera_distance(combined_bounds.size, aspect_ratio, camera.fov)
    var target := combined_bounds.get_center()
    camera.position = target + Vector3(0.0, maxf(combined_bounds.size.y * 0.12, 0.15), distance)
    camera.look_at(target, Vector3.UP)
    camera.near = 0.05
    camera.far = maxf(100.0, distance * 8.0)
    camera.current = true


func _play_scene() -> void:
    if scene_parser != null:
        scene_parser.play_scene()
