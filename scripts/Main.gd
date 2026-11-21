extends Node3D

var catalog_manager: CatalogManager
var scene_parser: SceneParser
var status_label: Label
var subtitle_label: RichTextLabel
var audio_player: AudioStreamPlayer
var import_dialog: FileDialog


func _ready() -> void:
    catalog_manager = CatalogManager.new()
    add_child(catalog_manager)
    scene_parser = SceneParser.new()
    add_child(scene_parser)
    scene_parser.world_root = get_node("World")
    _build_interface()
    scene_parser.subtitle_label = subtitle_label
    scene_parser.audio_player = audio_player
    var characters: Array[Dictionary] = catalog_manager.scan_catalog("res://assets/characters")
    var objects: Array[Dictionary] = catalog_manager.scan_catalog("res://assets/objects")
    status_label.text = "Catálogo: %d personajes · %d objetos" % [characters.size(), objects.size()]
    if scene_parser.load_scene_file("res://scenes/scene.example.json"):
        status_label.text = "Escena de ejemplo cargada"


func _build_interface() -> void:
    var layer := CanvasLayer.new()
    add_child(layer)
    var panel := PanelContainer.new()
    panel.position = Vector2(18, 18)
    panel.custom_minimum_size = Vector2(340, 150)
    layer.add_child(panel)
    var layout := VBoxContainer.new()
    panel.add_child(layout)

    var heading := Label.new()
    heading.text = "JEDL STUDIO"
    heading.add_theme_font_size_override("font_size", 22)
    layout.add_child(heading)

    var import_button := Button.new()
    import_button.text = "Importar JSON de escena"
    import_button.pressed.connect(_on_import_pressed)
    layout.add_child(import_button)

    var play_button := Button.new()
    play_button.text = "Reproducir escena"
    play_button.pressed.connect(_on_play_pressed)
    layout.add_child(play_button)

    status_label = Label.new()
    status_label.text = "Preparando estudio..."
    layout.add_child(status_label)

    subtitle_label = RichTextLabel.new()
    subtitle_label.position = Vector2(0, 0)
    subtitle_label.custom_minimum_size = Vector2(600, 70)
    subtitle_label.fit_content = true
    layout.add_child(subtitle_label)

    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)

    import_dialog = FileDialog.new()
    import_dialog.file_mode = FileDialog.FILE_MODE_OPEN_FILE
    import_dialog.access = FileDialog.ACCESS_FILESYSTEM
    import_dialog.add_filter("*.json", "Scene JSON")
    import_dialog.file_selected.connect(_on_scene_file_selected)
    layer.add_child(import_dialog)


func _on_import_pressed() -> void:
    import_dialog.popup_centered_ratio(0.8)


func _on_scene_file_selected(path: String) -> void:
    if scene_parser.load_scene_file(path):
        status_label.text = "JSON importado correctamente"
    else:
        status_label.text = "No se pudo cargar el JSON"


func _on_play_pressed() -> void:
    scene_parser.play_scene()
    status_label.text = "Reproduciendo escena"
