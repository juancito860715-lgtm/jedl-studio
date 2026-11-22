extends Node3D

const SceneParserScript = preload("res://scripts/SceneParser.gd")

var scene_parser: Node
var world_root: Node3D
var camera: Camera3D
var subtitle_label: Label
var audio_player: AudioStreamPlayer
var catalog_manager: Node
var gallery_panel: PanelContainer
var gallery_list: VBoxContainer
var gallery_title: Label
var json_panel: PanelContainer
var json_editor: TextEdit
var json_status: Label


func _ready() -> void:
    # Solicita orientación automática vertical y horizontal al iniciar.
    if OS.has_feature("android") or OS.has_feature("ios"):
        DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR)
    world_root = get_node_or_null("World") as Node3D
    if world_root == null:
        world_root = self
    camera = get_node_or_null("World/Camera3D") as Camera3D
    _build_overlay()
    catalog_manager = CatalogManager.new()
    add_child(catalog_manager)
    scene_parser = SceneParserScript.new()
    add_child(scene_parser)
    scene_parser.world_root = world_root
    scene_parser.camera = camera
    scene_parser.subtitle_label = subtitle_label
    scene_parser.audio_player = audio_player


func _build_overlay() -> void:
    var layer := CanvasLayer.new()
    layer.layer = 1
    add_child(layer)
    var screen := Control.new()
    screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    layer.add_child(screen)

    var header := PanelContainer.new()
    header.anchor_left = 0.0
    header.anchor_right = 1.0
    header.anchor_top = 0.0
    header.anchor_bottom = 0.0
    header.offset_left = 12.0
    header.offset_right = -12.0
    header.offset_top = 12.0
    header.offset_bottom = 78.0
    screen.add_child(header)
    var header_column := VBoxContainer.new()
    header.add_child(header_column)
    var heading := Label.new()
    heading.text = "JEDL Studio"
    heading.add_theme_font_size_override("font_size", 22)
    header_column.add_child(heading)
    subtitle_label = Label.new()
    subtitle_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    subtitle_label.add_theme_font_size_override("font_size", 16)
    header_column.add_child(subtitle_label)

    var toolbar := PanelContainer.new()
    toolbar.anchor_left = 0.0
    toolbar.anchor_right = 1.0
    toolbar.anchor_top = 1.0
    toolbar.anchor_bottom = 1.0
    toolbar.offset_left = 10.0
    toolbar.offset_right = -10.0
    toolbar.offset_top = -104.0
    toolbar.offset_bottom = -10.0
    screen.add_child(toolbar)
    var toolbar_row := HBoxContainer.new()
    toolbar_row.add_theme_constant_override("separation", 8)
    toolbar.add_child(toolbar_row)

    var load_button := Button.new()
    load_button.text = "Escena"
    load_button.pressed.connect(_load_example_scene)
    toolbar_row.add_child(load_button)
    var play_button := Button.new()
    play_button.text = "Reproducir"
    play_button.pressed.connect(_play_scene)
    toolbar_row.add_child(play_button)
    var gallery_2d_button := Button.new()
    gallery_2d_button.text = "Galería 2D"
    gallery_2d_button.pressed.connect(func(): _show_gallery("2d"))
    toolbar_row.add_child(gallery_2d_button)
    var gallery_3d_button := Button.new()
    gallery_3d_button.text = "Galería 3D"
    gallery_3d_button.pressed.connect(func(): _show_gallery("3d"))
    toolbar_row.add_child(gallery_3d_button)
    var json_button := Button.new()
    json_button.text = "Editor JSON"
    json_button.pressed.connect(_show_json_editor)
    toolbar_row.add_child(json_button)

    for button in toolbar_row.get_children():
        button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        button.custom_minimum_size = Vector2(0, 72)
        button.add_theme_font_size_override("font_size", 18)

    gallery_panel = PanelContainer.new()
    gallery_panel.anchor_left = 0.035
    gallery_panel.anchor_right = 0.965
    gallery_panel.anchor_top = 0.105
    gallery_panel.anchor_bottom = 0.91
    screen.add_child(gallery_panel)
    gallery_panel.visible = false

    json_panel = PanelContainer.new()
    json_panel.anchor_left = 0.025
    json_panel.anchor_right = 0.975
    json_panel.anchor_top = 0.08
    json_panel.anchor_bottom = 0.91
    screen.add_child(json_panel)
    json_panel.visible = false
    var json_column := VBoxContainer.new()
    json_column.add_theme_constant_override("separation", 8)
    json_panel.add_child(json_column)
    var json_header := HBoxContainer.new()
    json_column.add_child(json_header)
    var json_title := Label.new()
    json_title.text = "Editor de escenas JSON · JEDL v2"
    json_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    json_header.add_child(json_title)
    var json_close := Button.new()
    json_close.text = "Cerrar"
    json_close.pressed.connect(func(): json_panel.visible = false)
    json_header.add_child(json_close)
    json_editor = TextEdit.new()
    json_editor.size_flags_vertical = Control.SIZE_EXPAND_FILL
    json_editor.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    json_editor.add_theme_font_size_override("font_size", 14)
    json_editor.placeholder_text = "Escribe o pega aquí el JSON de la escena..."
    json_column.add_child(json_editor)
    var json_actions := HBoxContainer.new()
    json_column.add_child(json_actions)
    var validate_button := Button.new()
    validate_button.text = "Validar y cargar"
    validate_button.pressed.connect(_validate_and_load_json)
    json_actions.add_child(validate_button)
    var save_button := Button.new()
    save_button.text = "Guardar JSON local"
    save_button.pressed.connect(_save_json_locally)
    json_actions.add_child(save_button)
    json_status = Label.new()
    json_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    json_column.add_child(json_status)
    var gallery_column := VBoxContainer.new()
    gallery_column.add_theme_constant_override("separation", 10)
    gallery_panel.add_child(gallery_column)
    var gallery_header := HBoxContainer.new()
    gallery_column.add_child(gallery_header)
    gallery_title = Label.new()
    gallery_title.text = "Galería"
    gallery_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    gallery_title.add_theme_font_size_override("font_size", 21)
    gallery_header.add_child(gallery_title)
    var close_gallery := Button.new()
    close_gallery.text = "Cerrar"
    close_gallery.custom_minimum_size = Vector2(100, 54)
    close_gallery.add_theme_font_size_override("font_size", 18)
    close_gallery.pressed.connect(func(): gallery_panel.visible = false)
    gallery_header.add_child(close_gallery)
    var gallery_scroll := ScrollContainer.new()
    gallery_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    gallery_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    gallery_column.add_child(gallery_scroll)
    gallery_list = VBoxContainer.new()
    gallery_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    gallery_list.add_theme_constant_override("separation", 8)
    gallery_scroll.add_child(gallery_list)

    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)

func _show_json_editor() -> void:
    if json_panel == null or json_editor == null:
        return
    gallery_panel.visible = false
    if json_editor.text.is_empty():
        var file := FileAccess.open("res://scenes/scene.example.json", FileAccess.READ)
        if file != null:
            json_editor.text = file.get_as_text()
            file.close()
    json_status.text = "Contrato JEDL v2: background, characters, objects, elements, subtitles y sounds."
    json_panel.visible = true


func _validate_and_load_json() -> void:
    if scene_parser == null:
        return
    if scene_parser.load_scene_text(json_editor.text):
        json_status.text = "JSON válido: escena cargada correctamente."
        _frame_camera_to_content()
    else:
        json_status.text = "No se pudo cargar. Revisa la estructura JSON y las rutas res://."


func _save_json_locally() -> void:
    var file := FileAccess.open("user://scene_working.json", FileAccess.WRITE)
    if file == null:
        json_status.text = "No se pudo guardar el archivo local."
        return
    file.store_string(json_editor.text)
    file.close()
    json_status.text = "Guardado en user://scene_working.json"


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

func _show_gallery(kind: String) -> void:
    if gallery_panel == null or gallery_list == null or catalog_manager == null:
        return
    for child in gallery_list.get_children():
        child.queue_free()
    var entries: Array[Dictionary] = catalog_manager.scan_catalog(kind)
    gallery_title.text = (("Galería 2D · %d fondos fotográficos" % entries.size()) if kind == "2d" else ("Galería 3D · %d modelos" % entries.size())) + " · Poly Haven / CC0"
    if entries.is_empty():
        var empty_label := Label.new()
        empty_label.text = "No se encontraron recursos empaquetados."
        empty_label.add_theme_font_size_override("font_size", 18)
        gallery_list.add_child(empty_label)
    for index in range(mini(entries.size(), 300)):
        var item: Dictionary = entries[index]
        var item_row := HBoxContainer.new()
        item_row.add_theme_constant_override("separation", 10)
        gallery_list.add_child(item_row)
        if item.has("preview_path"):
            var preview := TextureRect.new()
            preview.custom_minimum_size = Vector2(124, 88)
            preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
            preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
            preview.texture = load(String(item["preview_path"])) as Texture2D
            item_row.add_child(preview)
        var add_button := Button.new()
        add_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        add_button.custom_minimum_size = Vector2(0, 64)
        add_button.add_theme_font_size_override("font_size", 17)
        add_button.text = String(item["title"]) + " · " + String(item["category"]) + "\n" + String(item.get("license", ""))
        var resource_path := String(item["path"])
        add_button.pressed.connect(_add_gallery_asset.bind(resource_path))
        item_row.add_child(add_button)
    gallery_panel.visible = true

func _add_gallery_asset(resource_path: String) -> void:
    if scene_parser != null and scene_parser.add_catalog_asset(resource_path):
        _frame_camera_to_content()
