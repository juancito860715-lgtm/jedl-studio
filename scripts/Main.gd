extends Node3D

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const ProductionEditorScript = preload("res://scripts/ProductionEditor.gd")

var scene_parser: Node
var world_root: Node3D
var camera: Camera3D
var subtitle_label: Label
var audio_player: AudioStreamPlayer
var catalog_manager: Node
var gallery_panel: PanelContainer
var gallery_list: VBoxContainer
var gallery_title: Label
var gallery_category_row: HFlowContainer
var json_panel: PanelContainer
var json_editor: TextEdit
var json_status: Label
var primary_buttons: Dictionary = {}
var production_editor: ProductionEditor
var production_panel: PanelContainer
var production_selection: OptionButton
var production_status: Label
var production_timeline: HSlider
var production_color: ColorPickerButton
var transform_inputs: Dictionary = {"position": [], "rotation": [], "scale": []}


func _ready() -> void:
    # Solicita orientación automática vertical y horizontal al iniciar.
    if OS.has_feature("android") or OS.has_feature("ios"):
        DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR)
    world_root = get_node_or_null("World") as Node3D
    if world_root == null:
        world_root = self
    camera = get_node_or_null("World/Camera3D") as Camera3D
    get_viewport().size_changed.connect(_on_viewport_size_changed)
    _build_overlay()
    catalog_manager = CatalogManager.new()
    add_child(catalog_manager)
    scene_parser = SceneParserScript.new()
    add_child(scene_parser)
    scene_parser.world_root = world_root
    scene_parser.camera = camera
    scene_parser.subtitle_label = subtitle_label
    scene_parser.audio_player = audio_player
    scene_parser.catalog_manager = catalog_manager
    production_editor = ProductionEditorScript.new() as ProductionEditor
    add_child(production_editor)
    production_editor.configure(world_root)
    # JEDL Studio siempre abre una composición nueva y vacía.
    if subtitle_label != null:
        subtitle_label.text = "Composición nueva · lienzo vacío"


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
    load_button.pressed.connect(_new_blank_scene)
    load_button.pressed.connect(_animate_button.bind(load_button))
    primary_buttons["scene"] = load_button
    toolbar_row.add_child(load_button)
    var play_button := Button.new()
    play_button.text = "Reproducir"
    play_button.pressed.connect(_play_scene)
    play_button.pressed.connect(_animate_button.bind(play_button))
    primary_buttons["play"] = play_button
    toolbar_row.add_child(play_button)
    var gallery_2d_button := Button.new()
    gallery_2d_button.text = "Galería 2D"
    gallery_2d_button.pressed.connect(func(): _show_gallery("2d"))
    gallery_2d_button.pressed.connect(_animate_button.bind(gallery_2d_button))
    primary_buttons["gallery_2d"] = gallery_2d_button
    toolbar_row.add_child(gallery_2d_button)
    var gallery_3d_button := Button.new()
    gallery_3d_button.text = "Galería 3D"
    gallery_3d_button.pressed.connect(func(): _show_gallery("3d"))
    gallery_3d_button.pressed.connect(_animate_button.bind(gallery_3d_button))
    primary_buttons["gallery_3d"] = gallery_3d_button
    toolbar_row.add_child(gallery_3d_button)
    var json_button := Button.new()
    json_button.text = "Editor JSON"
    json_button.pressed.connect(_show_json_editor)
    json_button.pressed.connect(_animate_button.bind(json_button))
    primary_buttons["json"] = json_button
    toolbar_row.add_child(json_button)
    var editor_3d_button := Button.new()
    editor_3d_button.text = "Editor 3D"
    editor_3d_button.pressed.connect(_show_production_editor)
    primary_buttons["editor_3d"] = editor_3d_button
    toolbar_row.add_child(editor_3d_button)

    for button in toolbar_row.get_children():
        button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        button.custom_minimum_size = Vector2(0, 76)
        button.add_theme_font_size_override("font_size", 17)
        button.focus_mode = Control.FOCUS_ALL
        button.mouse_filter = Control.MOUSE_FILTER_STOP

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
    gallery_category_row = HFlowContainer.new()
    gallery_category_row.add_theme_constant_override("separation", 6)
    gallery_column.add_child(gallery_category_row)
    for category_data in [
        {"label": "Personajes", "kind": "3d", "category": "Personajes animados"},
        {"label": "Vegetación", "kind": "3d", "category": "Árboles y vegetación"},
        {"label": "Troncos y rocas", "kind": "3d", "category": "Rocas y troncos"},
        {"label": "Mobiliario", "kind": "3d", "category": "Mobiliario"},
        {"label": "Utilería", "kind": "3d", "category": "Contenedores y utilería"}
    ]:
        var category_button := Button.new()
        category_button.text = String(category_data["label"])
        category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        category_button.pressed.connect(_show_gallery.bind(String(category_data["kind"]), String(category_data["category"])))
        gallery_category_row.add_child(category_button)

    var gallery_scroll := ScrollContainer.new()
    gallery_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    gallery_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    gallery_column.add_child(gallery_scroll)
    gallery_list = VBoxContainer.new()
    gallery_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    gallery_list.add_theme_constant_override("separation", 8)
    gallery_scroll.add_child(gallery_list)

    _build_production_panel(screen)
    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)

func _show_json_editor() -> void:
    if json_panel == null or json_editor == null:
        return
    gallery_panel.visible = false
    if json_editor.text.is_empty():
        json_editor.text = """{
  "version": 2,
  "title": "Nueva escena",
  "characters": [],
  "objects": [],
  "elements": [],
  "subtitles": [],
  "sounds": []
}"""
    json_status.text = "Composición vacía lista. Añade recursos o pega un JSON de escena."
    json_panel.visible = true
    json_panel.move_to_front()


func _validate_and_load_json() -> void:
    if scene_parser == null:
        return
    if scene_parser.load_scene_text(json_editor.text):
        json_status.text = "JSON válido: escena cargada correctamente."
        gallery_panel.visible = false
        json_panel.visible = false
        _frame_camera_to_content()
        if subtitle_label != null:
            subtitle_label.text = "Escena lista · %d elementos 3D" % scene_parser.active_instances.size()
    else:
        json_status.text = scene_parser.last_error if not scene_parser.last_error.is_empty() else "No se pudo cargar el JSON. Revisa el contrato y los assetId."


func _save_json_locally() -> void:
    var file := FileAccess.open("user://scene_working.json", FileAccess.WRITE)
    if file == null:
        json_status.text = "No se pudo guardar el archivo local."
        return
    file.store_string(json_editor.text)
    file.close()
    json_status.text = "Guardado en user://scene_working.json"


func _on_viewport_size_changed() -> void:
    # Los paneles usan anclajes relativos y se adaptan al cambio de orientación.
    pass


func _new_blank_scene() -> void:
    if gallery_panel != null:
        gallery_panel.visible = false
    if json_panel != null:
        json_panel.visible = false
    if production_panel != null:
        production_panel.visible = false
    if scene_parser == null:
        return
    scene_parser.stop_scene()
    var blank_json := """{
  "version": 2,
  "title": "Nueva escena",
  "characters": [],
  "objects": [],
  "elements": [],
  "subtitles": [],
  "sounds": []
}"""
    if json_editor != null:
        json_editor.text = blank_json
    if scene_parser.load_scene_text(blank_json):
        if camera != null:
            camera.current = true
        if subtitle_label != null:
            subtitle_label.text = "Lienzo vacío · añade recursos o importa un JSON"
        _refresh_production_selection()


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
    # Reproducir debe mostrar el visor, no dejar el editor o la galería encima.
    if gallery_panel != null:
        gallery_panel.visible = false
    if json_panel != null:
        json_panel.visible = false
    if production_panel != null:
        production_panel.visible = false
    if scene_parser == null:
        return
    if scene_parser.scene_data.is_empty():
        _new_blank_scene()
    _frame_camera_to_content()
    scene_parser.play_scene()
    if scene_parser.active_instances.is_empty() and subtitle_label != null:
        subtitle_label.text = "La escena está vacía · añade recursos o importa un JSON"

func _animate_button(button: Control) -> void:
    if not is_instance_valid(button):
        return
    var tween := create_tween()
    tween.tween_property(button, "scale", Vector2(0.96, 0.96), 0.07)
    tween.tween_property(button, "scale", Vector2.ONE, 0.12)


func _show_gallery(kind: String, category_filter: String = "") -> void:
    if gallery_panel == null or gallery_list == null or catalog_manager == null:
        return
    for child in gallery_list.get_children():
        gallery_list.remove_child(child)
        child.queue_free()
    var entries: Array[Dictionary] = catalog_manager.scan_catalog(kind, category_filter)
    gallery_category_row.visible = kind == "3d"
    var category_title := category_filter if not category_filter.is_empty() else ("Elementos 2D" if kind == "2d" else "Personajes y objetos 3D")
    gallery_title.text = "%s · %d recursos" % [category_title, entries.size()]
    if entries.is_empty():
        var empty_label := Label.new()
        var catalog_error: String = catalog_manager.get_catalog_error()
        empty_label.text = "No se pudieron cargar los recursos del inventario.\n" + catalog_error if not catalog_error.is_empty() else ("El banco de elementos 2D transparentes todavía no está instalado." if kind == "2d" else "Esta categoría aún no tiene recursos instalados.")
        empty_label.add_theme_font_size_override("font_size", 18)
        gallery_list.add_child(empty_label)
    for index in range(mini(entries.size(), 300)):
        var item: Dictionary = entries[index]
        var item_row := PanelContainer.new()
        item_row.custom_minimum_size = Vector2(0, 132)
        gallery_list.add_child(item_row)
        var card_row := HBoxContainer.new()
        card_row.add_theme_constant_override("separation", 12)
        item_row.add_child(card_row)
        var preview := TextureRect.new()
        preview.custom_minimum_size = Vector2(124, 112)
        preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
        preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
        preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
        var preview_path := String(item.get("preview_path", ""))
        if not preview_path.is_empty():
            preview.texture = load(preview_path) as Texture2D
        card_row.add_child(preview)
        var details := VBoxContainer.new()
        details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        details.size_flags_vertical = Control.SIZE_EXPAND_FILL
        card_row.add_child(details)
        var title_label := Label.new()
        title_label.text = String(item.get("title", "Recurso sin nombre"))
        title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
        title_label.add_theme_font_size_override("font_size", 17)
        details.add_child(title_label)
        var category_label := Label.new()
        category_label.text = String(item.get("category", "Sin categoría")) + " · " + String(item.get("format", ""))
        category_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
        details.add_child(category_label)
        var add_button := Button.new()
        add_button.text = "Añadir a escena"
        add_button.custom_minimum_size = Vector2(0, 52)
        add_button.pressed.connect(_animate_button.bind(add_button))
        var resource_path := String(item["path"])
        add_button.pressed.connect(_add_gallery_asset.bind(resource_path, String(item.get("id", ""))))
        details.add_child(add_button)
    if json_panel != null:
        json_panel.visible = false
    gallery_panel.visible = true
    gallery_panel.move_to_front()

func _add_gallery_asset(resource_path: String, asset_id: String = "") -> void:
    if scene_parser == null:
        return
    if scene_parser.add_catalog_asset(resource_path, asset_id):
        _frame_camera_to_content()
        if gallery_title != null:
            gallery_title.text = "Añadido a la escena: " + asset_id
        if subtitle_label != null:
            subtitle_label.text = "Recurso incorporado · " + asset_id
        _refresh_production_selection()
    elif subtitle_label != null:
        subtitle_label.text = "No se pudo incorporar el recurso: " + resource_path



func _build_production_panel(screen: Control) -> void:
    production_panel = PanelContainer.new()
    production_panel.anchor_left = 0.025
    production_panel.anchor_right = 0.975
    production_panel.anchor_top = 0.10
    production_panel.anchor_bottom = 0.90
    screen.add_child(production_panel)
    production_panel.visible = false

    var column := VBoxContainer.new()
    column.add_theme_constant_override("separation", 8)
    production_panel.add_child(column)
    var header := HBoxContainer.new()
    column.add_child(header)
    var heading := Label.new()
    heading.text = "Editor de producción 3D"
    heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    heading.add_theme_font_size_override("font_size", 20)
    header.add_child(heading)
    var close_button := Button.new()
    close_button.text = "Cerrar"
    close_button.pressed.connect(func(): production_panel.visible = false)
    header.add_child(close_button)

    var selection_row := HBoxContainer.new()
    column.add_child(selection_row)
    var selection_label := Label.new()
    selection_label.text = "Objeto"
    selection_row.add_child(selection_label)
    production_selection = OptionButton.new()
    production_selection.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    production_selection.item_selected.connect(_on_editor_selection_changed)
    selection_row.add_child(production_selection)
    var refresh_button := Button.new()
    refresh_button.text = "Actualizar"
    refresh_button.pressed.connect(_refresh_production_selection)
    selection_row.add_child(refresh_button)

    var transform_grid := GridContainer.new()
    transform_grid.columns = 4
    column.add_child(transform_grid)
    for heading_text in ["Transformación", "X", "Y", "Z"]:
        var heading_cell := Label.new()
        heading_cell.text = heading_text
        transform_grid.add_child(heading_cell)
    for property_name in ["position", "rotation", "scale"]:
        var row_label := Label.new()
        row_label.text = "Posición" if property_name == "position" else ("Rotación °" if property_name == "rotation" else "Escala")
        transform_grid.add_child(row_label)
        for axis in range(3):
            var spin := SpinBox.new()
            spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
            spin.min_value = -1000.0 if property_name != "scale" else 0.01
            spin.max_value = 1000.0
            spin.step = 0.05 if property_name != "rotation" else 1.0
            spin.value = 1.0 if property_name == "scale" else 0.0
            spin.value_changed.connect(_on_editor_transform_value_changed.bind(property_name, axis))
            transform_grid.add_child(spin)
            transform_inputs[property_name].append(spin)

    var material_row := HBoxContainer.new()
    column.add_child(material_row)
    var material_label := Label.new()
    material_label.text = "Color del material"
    material_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    material_row.add_child(material_label)
    production_color = ColorPickerButton.new()
    production_color.color = Color.WHITE
    production_color.color_changed.connect(_on_editor_color_changed)
    material_row.add_child(production_color)

    var timeline_label := Label.new()
    timeline_label.text = "Línea de tiempo · segundos"
    column.add_child(timeline_label)
    production_timeline = HSlider.new()
    production_timeline.min_value = 0.0
    production_timeline.max_value = 30.0
    production_timeline.step = 0.05
    production_timeline.value_changed.connect(_on_editor_timeline_changed)
    column.add_child(production_timeline)

    var timeline_actions := HBoxContainer.new()
    column.add_child(timeline_actions)
    var keyframe_button := Button.new()
    keyframe_button.text = "Añadir / actualizar fotograma clave"
    keyframe_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    keyframe_button.pressed.connect(_add_editor_keyframe)
    timeline_actions.add_child(keyframe_button)
    production_status = Label.new()
    production_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    production_status.text = "Selecciona un modelo de la escena para editar sus transformaciones, material y animación."
    column.add_child(production_status)


func _show_production_editor() -> void:
    if production_panel == null:
        return
    if gallery_panel != null:
        gallery_panel.visible = false
    if json_panel != null:
        json_panel.visible = false
    _refresh_production_selection()
    production_panel.visible = true
    production_panel.move_to_front()


func _refresh_production_selection() -> void:
    if production_selection == null or scene_parser == null:
        return
    production_selection.clear()
    for instance in scene_parser.active_instances:
        if is_instance_valid(instance):
            production_selection.add_item(instance.name)
    if production_selection.item_count > 0:
        production_selection.select(0)
        _on_editor_selection_changed(0)
    elif production_status != null:
        production_status.text = "La escena no contiene modelos 3D. Añade un modelo desde la galería."


func _on_editor_selection_changed(index: int) -> void:
    if scene_parser == null or production_editor == null:
        return
    if index < 0 or index >= scene_parser.active_instances.size():
        return
    var selected: Node3D = scene_parser.active_instances[index]
    if not production_editor.select_node(selected):
        return
    var values := {
        "position": selected.position,
        "rotation": selected.rotation_degrees,
        "scale": selected.scale
    }
    for property_name in ["position", "rotation", "scale"]:
        var vector: Vector3 = values[property_name]
        for axis in range(3):
            var spin: SpinBox = transform_inputs[property_name][axis]
            spin.set_value_no_signal(vector[axis])
    if production_status != null:
        production_status.text = "Editando: " + selected.name


func _on_editor_transform_value_changed(value: float, property_name: String, axis: int) -> void:
    if production_editor == null or production_editor.selected_node == null:
        return
    var selected: Node3D = production_editor.selected_node
    var position_value := selected.position
    var rotation_value := selected.rotation_degrees
    var scale_value := selected.scale
    if property_name == "position":
        if axis == 0: position_value.x = value
        elif axis == 1: position_value.y = value
        else: position_value.z = value
    elif property_name == "rotation":
        if axis == 0: rotation_value.x = value
        elif axis == 1: rotation_value.y = value
        else: rotation_value.z = value
    elif property_name == "scale":
        if axis == 0: scale_value.x = value
        elif axis == 1: scale_value.y = value
        else: scale_value.z = value
    if production_editor.set_transform(position_value, rotation_value, scale_value):
        production_status.text = "Transformación aplicada a " + selected.name
    else:
        production_status.text = production_editor.last_error


func _on_editor_color_changed(color: Color) -> void:
    if production_editor == null:
        return
    if production_editor.set_material_color(color):
        production_status.text = "Color del material aplicado."
    else:
        production_status.text = production_editor.last_error


func _on_editor_timeline_changed(value: float) -> void:
    if production_editor == null:
        return
    if not production_editor.scrub_timeline(value):
        production_status.text = production_editor.last_error


func _add_editor_keyframe() -> void:
    if production_editor == null or production_timeline == null:
        return
    if production_editor.add_transform_keyframe(production_timeline.value):
        production_timeline.max_value = maxf(30.0, production_editor.get_timeline_length())
        production_status.text = "Fotograma clave guardado en %.2f s." % production_timeline.value
    else:
        production_status.text = production_editor.last_error
