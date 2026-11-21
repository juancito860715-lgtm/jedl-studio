extends Node3D

const SceneParserScript = preload("res://scripts/SceneParser.gd")

var scene_parser: Node
var world_root: Node3D
var subtitle_label: Label
var audio_player: AudioStreamPlayer


func _ready() -> void:
    world_root = get_node_or_null("World") as Node3D
    if world_root == null:
        world_root = self
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
    if scene_parser != null:
        scene_parser.load_scene_file("res://scenes/scene.example.json")


func _play_scene() -> void:
    if scene_parser != null:
        scene_parser.play_scene()
