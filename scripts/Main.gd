extends Node3D

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const ProjectStoreScript = preload("res://scripts/ProjectStore.gd")
const EditorSelectionScript = preload("res://scripts/EditorSelection.gd")
const GestureControllerScript = preload("res://scripts/TouchGestureController.gd")
const EditorPanelScript = preload("res://scripts/Editor2DPanel.gd")

var scene_parser: Node
var world_root: Node3D
var canvas_2d_layer: CanvasLayer
var canvas_2d_root: Node2D
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
var primary_buttons: Dictionary = {}
var missing_alternative_button: Button
var missing_cancel_button: Button
var timeline_panel: PanelContainer
var timeline_target_option: OptionButton
var timeline_property_option: OptionButton
var timeline_time_spin: SpinBox
var timeline_old_time_spin: SpinBox
var timeline_value_spins: Array[SpinBox] = []
var timeline_slider: HSlider
var timeline_tracks_list: VBoxContainer
var timeline_status: Label
var pending_scene_backup: Dictionary = {}
var choosing_missing_alternative := false
var overlay_screen: Control
var editor_2d_panel: Editor2DPanel
var gesture_controller: TouchGestureController
var selected_2d_node: Node2D


func _ready() -> void:
	# Solicita orientación automática vertical y horizontal al iniciar.
	if OS.has_feature("android") or OS.has_feature("ios"):
		DisplayServer.screen_set_orientation(DisplayServer.SCREEN_SENSOR)
	world_root = get_node_or_null("World") as Node3D
	if world_root == null:
		world_root = self
	canvas_2d_layer = CanvasLayer.new()
	canvas_2d_layer.name = "Independent2DCanvasLayer"
	canvas_2d_layer.layer = 0
	add_child(canvas_2d_layer)
	canvas_2d_root = Node2D.new()
	canvas_2d_root.name = "Independent2DCanvas"
	canvas_2d_layer.add_child(canvas_2d_root)
	_update_2d_canvas_layout()
	camera = get_node_or_null("World/Camera3D") as Camera3D
	get_viewport().size_changed.connect(_on_viewport_size_changed)
	_build_overlay()
	catalog_manager = CatalogManager.new()
	add_child(catalog_manager)
	scene_parser = SceneParserScript.new()
	add_child(scene_parser)
	scene_parser.world_root = world_root
	scene_parser.canvas_root = canvas_2d_root
	scene_parser.camera = camera
	scene_parser.subtitle_label = subtitle_label
	scene_parser.audio_player = audio_player
	scene_parser.catalog_manager = catalog_manager
	scene_parser.scene_data = _blank_scene_document()
	if scene_parser.timeline_engine != null:
		scene_parser.timeline_engine.playhead_changed.connect(_on_timeline_playhead_changed)
	gesture_controller = GestureControllerScript.new()
	editor_2d_panel = EditorPanelScript.new()
	editor_2d_panel.name = "Editor2DPanel"
	editor_2d_panel.anchor_left = 0.025
	editor_2d_panel.anchor_right = 0.975
	editor_2d_panel.anchor_top = 0.10
	editor_2d_panel.anchor_bottom = 0.90
	overlay_screen.add_child(editor_2d_panel)
	editor_2d_panel.configure(scene_parser, canvas_2d_root)
	editor_2d_panel.close_requested.connect(func(): editor_2d_panel.visible = false)
	editor_2d_panel.visible = false
	subtitle_label.text = "Proyecto nuevo · escena vacía. Carga un JSON o añade recursos desde las galerías."


func _build_overlay() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 1
	add_child(layer)
	var screen := Control.new()
	screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.add_child(screen)
	overlay_screen = screen

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
	gallery_2d_button.text = "Elementos 2D"
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
	var timeline_button := Button.new()
	timeline_button.text = "Timeline"
	timeline_button.pressed.connect(_show_timeline_panel)
	timeline_button.pressed.connect(_animate_button.bind(timeline_button))
	primary_buttons["timeline"] = timeline_button
	toolbar_row.add_child(timeline_button)
	var editor_2d_button := Button.new()
	editor_2d_button.text = "Editor de elementos 2D"
	editor_2d_button.pressed.connect(_show_editor_2d_panel)
	editor_2d_button.pressed.connect(_animate_button.bind(editor_2d_button))
	primary_buttons["editor_2d"] = editor_2d_button
	toolbar_row.add_child(editor_2d_button)

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
	var missing_actions := HBoxContainer.new()
	json_column.add_child(missing_actions)
	missing_alternative_button = Button.new()
	missing_alternative_button.text = "Elegir otro recurso de la misma categoría"
	missing_alternative_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	missing_alternative_button.visible = false
	missing_alternative_button.pressed.connect(_choose_missing_alternative)
	missing_actions.add_child(missing_alternative_button)
	missing_cancel_button = Button.new()
	missing_cancel_button.text = "Cancelar"
	missing_cancel_button.visible = false
	missing_cancel_button.pressed.connect(_cancel_missing_resource)
	missing_actions.add_child(missing_cancel_button)
	var project_actions := HBoxContainer.new()
	json_column.add_child(project_actions)
	var save_project_button := Button.new()
	save_project_button.text = "Guardar proyecto"
	save_project_button.pressed.connect(_save_project)
	project_actions.add_child(save_project_button)
	var open_project_button := Button.new()
	open_project_button.text = "Abrir guardado"
	open_project_button.pressed.connect(_open_saved_project)
	project_actions.add_child(open_project_button)
	var restore_project_button := Button.new()
	restore_project_button.text = "Restaurar versión anterior"
	restore_project_button.pressed.connect(_restore_project)
	project_actions.add_child(restore_project_button)
	var duplicate_project_button := Button.new()
	duplicate_project_button.text = "Duplicar"
	duplicate_project_button.pressed.connect(_duplicate_project)
	project_actions.add_child(duplicate_project_button)
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
	var category_row := HFlowContainer.new()
	category_row.add_theme_constant_override("separation", 6)
	gallery_column.add_child(category_row)
	for category_data in [
		{"label": "Elementos 2D", "kind": "2d", "category": "Elementos 2D"},
		{"label": "Personajes 3D", "kind": "3d", "category": "Personajes 3D"}
	]:
		var category_button := Button.new()
		category_button.text = String(category_data["label"])
		category_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		category_button.pressed.connect(_show_gallery.bind(String(category_data["kind"]), String(category_data["category"])))
		category_row.add_child(category_button)

	var gallery_scroll := ScrollContainer.new()
	gallery_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	gallery_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gallery_column.add_child(gallery_scroll)
	gallery_list = VBoxContainer.new()
	gallery_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gallery_list.add_theme_constant_override("separation", 8)
	gallery_scroll.add_child(gallery_list)
	_build_timeline_panel(screen)

	audio_player = AudioStreamPlayer.new()
	add_child(audio_player)

func _show_editor_2d_panel() -> void:
	if editor_2d_panel == null:
		return
	if gallery_panel != null:
		gallery_panel.visible = false
	if json_panel != null:
		json_panel.visible = false
	if timeline_panel != null:
		timeline_panel.visible = false
	editor_2d_panel.visible = true
	editor_2d_panel.move_to_front()


func _unhandled_input(event: InputEvent) -> void:
	if editor_2d_panel == null or not editor_2d_panel.visible or gesture_controller == null:
		return
	if event is InputEventScreenTouch:
		var touch := event as InputEventScreenTouch
		if touch.pressed and touch.index == 0:
			selected_2d_node = _select_2d_node_at(touch.position)
			editor_2d_panel.set_selected_node(selected_2d_node)
		if selected_2d_node != null:
			_update_gesture_coordinate_transform()
			gesture_controller.handle_event(event, selected_2d_node)
			_sync_selected_2d_scene_entry()
		else:
			gesture_controller.reset()
	elif event is InputEventScreenDrag and selected_2d_node != null:
		_update_gesture_coordinate_transform()
		gesture_controller.handle_event(event, selected_2d_node)
		_sync_selected_2d_scene_entry()


func _update_gesture_coordinate_transform() -> void:
	if canvas_2d_root == null or gesture_controller == null:
		return
	var canvas_transform: Transform2D = canvas_2d_root.get_global_transform_with_canvas()
	if absf(canvas_transform.determinant()) > 0.000001:
		gesture_controller.coordinate_transform = canvas_transform.affine_inverse()
	else:
		gesture_controller.coordinate_transform = Transform2D.IDENTITY


func _select_2d_node_at(viewport_position: Vector2) -> Node2D:
	if canvas_2d_root == null:
		return null
	var local_position := canvas_2d_root.make_canvas_position_local(viewport_position)
	var items: Array = []
	var nodes_by_id: Dictionary = {}
	var draw_order := 0
	for child in canvas_2d_root.get_children():
		if not (child is Node2D):
			continue
		var node := child as Node2D
		var entry_id := String(node.get_meta("jedl_entry_id", node.name))
		var bounds := _selection_bounds_for_node(node)
		items.append({
			"id": entry_id,
			"position": node.position,
			"scale": node.scale,
			"rotation": node.rotation,
			"offset": bounds.get("offset", Vector2.ZERO),
			"size": bounds.get("size", Vector2(64.0, 64.0)),
			"z_index": node.z_index,
			"draw_order": draw_order
		})
		nodes_by_id[entry_id] = node
		draw_order += 1
	var selected_id := EditorSelectionScript.select_element(items, local_position)
	return nodes_by_id.get(selected_id) as Node2D


func _selection_bounds_for_node(node: Node2D) -> Dictionary:
	if node is Sprite2D:
		var sprite := node as Sprite2D
		if sprite.texture != null:
			var rect := sprite.get_rect()
			return {"size": rect.size, "offset": rect.position + rect.size * 0.5}
	var vertices: Array[Vector2] = []
	if node is Polygon2D:
		for vertex in (node as Polygon2D).polygon:
			vertices.append(vertex)
	else:
		for candidate in node.find_children("*", "Polygon2D", true, false):
			var polygon_node := candidate as Polygon2D
			for vertex in polygon_node.polygon:
				vertices.append(node.to_local(polygon_node.to_global(vertex)))
	if vertices.is_empty():
		return {"size": Vector2(64.0, 64.0), "offset": Vector2.ZERO}
	var minimum := vertices[0]
	var maximum := vertices[0]
	for vertex in vertices:
		minimum.x = minf(minimum.x, vertex.x)
		minimum.y = minf(minimum.y, vertex.y)
		maximum.x = maxf(maximum.x, vertex.x)
		maximum.y = maxf(maximum.y, vertex.y)
	return {"size": maximum - minimum, "offset": (minimum + maximum) * 0.5}


func _sync_selected_2d_scene_entry() -> void:
	if selected_2d_node == null or scene_parser == null:
		return
	var entry_id := String(selected_2d_node.get_meta("jedl_entry_id", selected_2d_node.name))
	for collection_name in ["elements"]:
		var collection: Variant = scene_parser.scene_data.get(collection_name, [])
		if not (collection is Array):
			continue
		for entry_value in collection:
			if entry_value is Dictionary and String(entry_value.get("id", "")) == entry_id:
				gesture_controller.sync_scene_entry(entry_value, selected_2d_node)
				return


func _show_json_editor() -> void:
	if json_panel == null or json_editor == null:
		return
	gallery_panel.visible = false
	if json_editor.text.is_empty():
		json_editor.text = JSON.stringify(_blank_scene_document(), "\t")
	json_status.text = "Contrato JEDL v2: personajes 2.5D/3D riggeados, objects, elements, actions, subtitles y sounds."
	json_panel.visible = true
	json_panel.move_to_front()


func _validate_and_load_json() -> void:
	if scene_parser == null:
		return
	if pending_scene_backup.is_empty():
		pending_scene_backup = scene_parser.scene_data.duplicate(true)
	if scene_parser.load_scene_text(json_editor.text):
		json_status.text = "JSON válido: escena cargada correctamente."
		pending_scene_backup.clear()
		choosing_missing_alternative = false
		gallery_panel.visible = false
		json_panel.visible = false
		_frame_camera_to_content()
		if missing_alternative_button != null:
			missing_alternative_button.visible = false
			missing_cancel_button.visible = false
		_refresh_timeline_targets()
		if subtitle_label != null:
			subtitle_label.text = "Escena lista · %d elementos" % scene_parser.active_instances.size()
	else:
		json_status.text = scene_parser.last_error if not scene_parser.last_error.is_empty() else "No se pudo cargar el JSON. Revisa el contrato y los assetId."
		if scene_parser.last_missing_category != "":
			json_status.text += "\nPuedes elegir otro recurso de la misma categoría o cancelar la carga."
			missing_alternative_button.visible = true
			missing_cancel_button.visible = true


func _save_json_locally() -> void:
	var file := FileAccess.open("user://scene_working.json", FileAccess.WRITE)
	if file == null:
		json_status.text = "No se pudo guardar el archivo local."
		return
	file.store_string(json_editor.text)
	file.close()
	json_status.text = "Guardado en user://scene_working.json"


func _on_viewport_size_changed() -> void:
	_update_2d_canvas_layout()
	if scene_parser != null:
		scene_parser._fit_background_to_camera()


func _update_2d_canvas_layout() -> void:
	if canvas_2d_root == null:
		return
	var viewport_size := get_viewport().get_visible_rect().size
	canvas_2d_root.position = viewport_size * 0.5
	canvas_2d_root.scale = Vector2.ONE


func _load_example_scene() -> void:
	# Escena es el retorno al visor: cierra cualquier panel que pudiera tapar el mundo 3D.
	if gallery_panel != null:
		gallery_panel.visible = false
	if json_panel != null:
		json_panel.visible = false
	if scene_parser == null:
		return
	scene_parser.stop_scene()
	if camera != null:
		camera.current = true
	if scene_parser.load_scene_file("res://scenes/scene.example.json"):
		pending_scene_backup.clear()
		_refresh_timeline_targets()
		_frame_camera_to_content()
		if subtitle_label != null:
			subtitle_label.text = "Escena cargada · %d elementos" % scene_parser.active_instances.size()
	elif subtitle_label != null:
		subtitle_label.text = "Error: no se pudo cargar la escena de ejemplo."


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
	if scene_parser == null:
		return
	_frame_camera_to_content()
	scene_parser.play_scene()

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
	var category_title := category_filter if not category_filter.is_empty() else ("Elementos 2D" if kind == "2d" else "Personajes y objetos 3D")
	gallery_title.text = "%s · %d recursos" % [category_title, entries.size()]
	if entries.is_empty():
		var empty_label := Label.new()
		var catalog_error: String = catalog_manager.get_catalog_error()
		empty_label.text = "No se pudieron cargar los recursos del inventario.\n" + catalog_error if not catalog_error.is_empty() else "Esta categoría aún no tiene recursos individuales instalados.\nEl inventario no contiene elementos para este filtro."
		empty_label.add_theme_font_size_override("font_size", 18)
		gallery_list.add_child(empty_label)
	for index in range(mini(entries.size(), 24)):
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
		var is_background := false
		add_button.pressed.connect(_add_gallery_asset.bind(resource_path, is_background, String(item.get("id", ""))))
		details.add_child(add_button)
	if json_panel != null:
		json_panel.visible = false
	gallery_panel.visible = true
	gallery_panel.move_to_front()

func _add_gallery_asset(resource_path: String, is_background: bool = true, asset_id: String = "") -> void:
	if scene_parser == null:
		return
	if choosing_missing_alternative:
		var parsed: Variant = JSON.parse_string(json_editor.text)
		var replaced := false
		if parsed is Dictionary:
			for collection_name in ["characters", "objects", "elements"]:
				var collection: Variant = parsed.get(collection_name, [])
				if collection is Array:
					for entry in collection:
						if entry is Dictionary and String(entry.get("id", "")) == scene_parser.last_missing_entry_id:
							entry["assetId"] = asset_id
							entry.erase("path")
							entry["kind"] = scene_parser.last_missing_kind
							entry["category"] = scene_parser.last_missing_category
							replaced = true
		if replaced:
			json_editor.text = JSON.stringify(parsed, "\t")
			choosing_missing_alternative = false
			_validate_and_load_json()
		elif subtitle_label != null:
			subtitle_label.text = "No se encontró el elemento JSON que requiere el recurso alternativo."
		return
	if scene_parser.add_catalog_asset(resource_path, false, asset_id):
		_frame_camera_to_content()
		_refresh_timeline_targets()
		if gallery_title != null:
			gallery_title.text = "Añadido a la escena: " + asset_id
		if subtitle_label != null:
			subtitle_label.text = "Recurso incorporado · " + asset_id
	elif subtitle_label != null:
		subtitle_label.text = "No se pudo incorporar el recurso: " + resource_path


func _choose_missing_alternative() -> void:
	if scene_parser == null:
		return
	choosing_missing_alternative = true
	json_panel.visible = false
	_show_gallery(scene_parser.last_missing_kind, scene_parser.last_missing_category)


func _cancel_missing_resource() -> void:
	if not pending_scene_backup.is_empty():
		scene_parser.load_scene_text(JSON.stringify(pending_scene_backup))
		json_editor.text = JSON.stringify(pending_scene_backup, "\t")
		_refresh_timeline_targets()
	pending_scene_backup.clear()
	choosing_missing_alternative = false
	if missing_alternative_button != null:
		missing_alternative_button.visible = false
		missing_cancel_button.visible = false
	if json_status != null:
		json_status.text = "Carga cancelada. Se conservó la escena anterior."


func _build_timeline_panel(screen: Control) -> void:
	timeline_panel = PanelContainer.new()
	timeline_panel.anchor_left = 0.025
	timeline_panel.anchor_right = 0.975
	timeline_panel.anchor_top = 0.10
	timeline_panel.anchor_bottom = 0.90
	screen.add_child(timeline_panel)
	timeline_panel.visible = false
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	timeline_panel.add_child(column)
	var header := HBoxContainer.new()
	column.add_child(header)
	var heading := Label.new()
	heading.text = "Timeline compartido · JSON y keyframes manuales"
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(heading)
	var close_button := Button.new()
	close_button.text = "Cerrar"
	close_button.pressed.connect(func(): timeline_panel.visible = false)
	header.add_child(close_button)
	timeline_target_option = OptionButton.new()
	timeline_target_option.item_selected.connect(_on_timeline_target_selected)
	column.add_child(timeline_target_option)
	timeline_property_option = OptionButton.new()
	timeline_property_option.add_item("Posición", 0)
	timeline_property_option.add_item("Rotación", 1)
	timeline_property_option.add_item("Escala", 2)
	timeline_property_option.item_selected.connect(func(_index: int): _sync_timeline_values())
	column.add_child(timeline_property_option)
	var time_row := HBoxContainer.new()
	column.add_child(time_row)
	var time_label := Label.new()
	time_label.text = "Tiempo (s)"
	time_row.add_child(time_label)
	timeline_time_spin = SpinBox.new()
	timeline_time_spin.min_value = 0.0
	timeline_time_spin.max_value = 600.0
	timeline_time_spin.step = 0.05
	timeline_time_spin.value = 0.0
	timeline_time_spin.value_changed.connect(_seek_timeline)
	timeline_time_spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	time_row.add_child(timeline_time_spin)
	var value_row := HBoxContainer.new()
	column.add_child(value_row)
	timeline_value_spins.clear()
	for axis_name in ["X", "Y", "Z"]:
		var axis_column := VBoxContainer.new()
		axis_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		value_row.add_child(axis_column)
		var axis_label := Label.new()
		axis_label.text = axis_name
		axis_column.add_child(axis_label)
		var spin := SpinBox.new()
		spin.min_value = -1000.0
		spin.max_value = 1000.0
		spin.step = 0.05
		spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		axis_column.add_child(spin)
		timeline_value_spins.append(spin)
	var old_time_row := HBoxContainer.new()
	column.add_child(old_time_row)
	var old_time_label := Label.new()
	old_time_label.text = "Mover desde (s)"
	old_time_row.add_child(old_time_label)
	timeline_old_time_spin = SpinBox.new()
	timeline_old_time_spin.min_value = 0.0
	timeline_old_time_spin.max_value = 600.0
	timeline_old_time_spin.step = 0.05
	timeline_old_time_spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	old_time_row.add_child(timeline_old_time_spin)
	var key_actions := HBoxContainer.new()
	column.add_child(key_actions)
	var add_key_button := Button.new()
	add_key_button.text = "Crear"
	add_key_button.pressed.connect(_add_manual_keyframe)
	key_actions.add_child(add_key_button)
	var edit_key_button := Button.new()
	edit_key_button.text = "Editar valor"
	edit_key_button.pressed.connect(_edit_manual_keyframe)
	key_actions.add_child(edit_key_button)
	var move_key_button := Button.new()
	move_key_button.text = "Mover"
	move_key_button.pressed.connect(_move_manual_keyframe)
	key_actions.add_child(move_key_button)
	var delete_key_button := Button.new()
	delete_key_button.text = "Eliminar"
	delete_key_button.pressed.connect(_delete_manual_keyframe)
	key_actions.add_child(delete_key_button)
	var tracks_heading := Label.new()
	tracks_heading.text = "Pistas y marcadores · selecciona un punto para editarlo"
	column.add_child(tracks_heading)
	var tracks_scroll := ScrollContainer.new()
	tracks_scroll.custom_minimum_size = Vector2(0, 110)
	tracks_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(tracks_scroll)
	timeline_tracks_list = VBoxContainer.new()
	timeline_tracks_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tracks_scroll.add_child(timeline_tracks_list)
	timeline_slider = HSlider.new()
	timeline_slider.min_value = 0.0
	timeline_slider.max_value = 1.0
	timeline_slider.step = 0.01
	timeline_slider.value_changed.connect(_seek_timeline)
	column.add_child(timeline_slider)
	var transport := HBoxContainer.new()
	column.add_child(transport)
	var play_button := Button.new()
	play_button.text = "Reproducir"
	play_button.pressed.connect(_play_timeline)
	transport.add_child(play_button)
	var pause_button := Button.new()
	pause_button.text = "Pausar"
	pause_button.pressed.connect(_pause_timeline)
	transport.add_child(pause_button)
	var stop_button := Button.new()
	stop_button.text = "Detener"
	stop_button.pressed.connect(_stop_timeline)
	transport.add_child(stop_button)
	timeline_status = Label.new()
	timeline_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(timeline_status)


func _show_timeline_panel() -> void:
	if timeline_panel == null:
		return
	gallery_panel.visible = false
	json_panel.visible = false
	_refresh_timeline_targets()
	timeline_panel.visible = true
	timeline_panel.move_to_front()


func _refresh_timeline_targets() -> void:
	if timeline_target_option == null or scene_parser == null:
		return
	timeline_target_option.clear()
	for instance in scene_parser.active_instances:
		if not is_instance_valid(instance):
			continue
		var target_id := String(instance.get_meta("jedl_entry_id", instance.name))
		timeline_target_option.add_item(instance.name)
		timeline_target_option.set_item_metadata(timeline_target_option.item_count - 1, target_id)
	var engine = scene_parser.timeline_engine
	if engine != null and timeline_slider != null:
		timeline_slider.max_value = maxf(0.01, float(engine.duration_seconds))
		timeline_slider.set_value_no_signal(float(engine.playhead_seconds))
		timeline_status.text = "%d keyframes · duración %.2f s" % [engine.get_keyframe_count(), engine.duration_seconds]
	if timeline_target_option.item_count > 0:
		_on_timeline_target_selected(0)
	_refresh_timeline_tracks()


func _refresh_timeline_tracks() -> void:
	if timeline_tracks_list == null or scene_parser == null or scene_parser.timeline_engine == null:
		return
	for child in timeline_tracks_list.get_children():
		timeline_tracks_list.remove_child(child)
		child.queue_free()
	var tracks: Array[Dictionary] = scene_parser.timeline_engine.get_tracks_snapshot()
	if tracks.is_empty():
		var empty_label := Label.new()
		empty_label.text = "Sin keyframes. Selecciona un elemento y crea el primer punto."
		timeline_tracks_list.add_child(empty_label)
		return
	for track in tracks:
		var target_id := String(track.get("target_id", ""))
		var property_name := String(track.get("property", ""))
		var target_label := target_id
		for instance in scene_parser.active_instances:
			if is_instance_valid(instance) and String(instance.get_meta("jedl_entry_id", instance.name)) == target_id:
				target_label = instance.name
				break
		var row := HBoxContainer.new()
		timeline_tracks_list.add_child(row)
		var heading := Label.new()
		heading.text = "%s · %s" % [target_label, property_name]
		heading.custom_minimum_size = Vector2(145, 0)
		row.add_child(heading)
		for key in track.get("keyframes", []):
			var key_time := float(key.get("time", 0.0))
			var marker := Button.new()
			marker.text = "%.2fs" % key_time
			marker.tooltip_text = "Seleccionar keyframe · %s" % str(key.get("value", []))
			marker.custom_minimum_size = Vector2(76, 42)
			marker.pressed.connect(_select_timeline_keyframe.bind(target_id, property_name, key_time))
			row.add_child(marker)


func _select_timeline_keyframe(target_id: String, property_name: String, key_time: float) -> void:
	for index in range(timeline_target_option.item_count):
		if String(timeline_target_option.get_item_metadata(index)) == target_id:
			timeline_target_option.select(index)
			break
	var property_index := ["position", "rotation_degrees", "scale"].find(property_name)
	if property_index >= 0:
		timeline_property_option.select(property_index)
	timeline_time_spin.set_value_no_signal(key_time)
	_seek_timeline(key_time)
	_sync_timeline_values()


func _on_timeline_playhead_changed(seconds: float) -> void:
	if timeline_slider == null:
		return
	timeline_slider.set_value_no_signal(seconds)
	timeline_time_spin.set_value_no_signal(seconds)
	_sync_timeline_values()


func _on_timeline_target_selected(index: int) -> void:
	if timeline_target_option == null or scene_parser == null or index < 0:
		return
	var target_id := String(timeline_target_option.get_item_metadata(index))
	for instance in scene_parser.active_instances:
		if not is_instance_valid(instance) or String(instance.get_meta("jedl_entry_id", instance.name)) != target_id:
			continue
		var vector := Vector3.ZERO
		if instance is Node2D:
			var canvas_instance := instance as Node2D
			match timeline_property_option.selected:
				0:
					vector = Vector3(canvas_instance.position.x / 100.0, -canvas_instance.position.y / 100.0, 0.0)
				1:
					vector = Vector3(0.0, 0.0, canvas_instance.rotation_degrees)
				2:
					vector = Vector3(canvas_instance.scale.x, canvas_instance.scale.y, 1.0)
		elif instance is Node3D:
			var stage_instance := instance as Node3D
			match timeline_property_option.selected:
				0:
					vector = stage_instance.position
				1:
					vector = stage_instance.rotation_degrees
				2:
					vector = stage_instance.scale
		for axis in range(3):
			timeline_value_spins[axis].set_value_no_signal(vector[axis])
		return


func _sync_timeline_values() -> void:
	if timeline_target_option == null or timeline_target_option.item_count == 0:
		return
	_on_timeline_target_selected(timeline_target_option.selected)


func _add_manual_keyframe() -> void:
	if scene_parser == null or timeline_target_option.item_count == 0:
		timeline_status.text = "Añade primero un elemento a la escena."
		return
	var target_id := String(timeline_target_option.get_item_metadata(timeline_target_option.selected))
	var property_name: String = String(["position", "rotation_degrees", "scale"][timeline_property_option.selected])
	var value := Vector3(timeline_value_spins[0].value, timeline_value_spins[1].value, timeline_value_spins[2].value)
	var engine = scene_parser.timeline_engine
	if engine.add_keyframe(target_id, property_name, timeline_time_spin.value, value):
		timeline_slider.max_value = maxf(0.01, float(engine.duration_seconds))
		timeline_status.text = "Keyframe guardado · %d keyframes" % engine.get_keyframe_count()
		_refresh_timeline_tracks()
	else:
		timeline_status.text = engine.last_error


func _edit_manual_keyframe() -> void:
	if scene_parser == null or timeline_target_option.item_count == 0:
		return
	var target_id := String(timeline_target_option.get_item_metadata(timeline_target_option.selected))
	var property_name: String = String(["position", "rotation_degrees", "scale"][timeline_property_option.selected])
	var value := Vector3(timeline_value_spins[0].value, timeline_value_spins[1].value, timeline_value_spins[2].value)
	var engine = scene_parser.timeline_engine
	if engine.edit_keyframe(target_id, property_name, timeline_time_spin.value, value):
		timeline_status.text = "Valor del keyframe actualizado."
		_refresh_timeline_tracks()
	else:
		timeline_status.text = engine.last_error


func _move_manual_keyframe() -> void:
	if scene_parser == null or timeline_target_option.item_count == 0:
		return
	var target_id := String(timeline_target_option.get_item_metadata(timeline_target_option.selected))
	var property_name: String = String(["position", "rotation_degrees", "scale"][timeline_property_option.selected])
	var engine = scene_parser.timeline_engine
	if engine.move_keyframe(target_id, property_name, timeline_old_time_spin.value, timeline_time_spin.value):
		timeline_slider.max_value = maxf(0.01, float(engine.duration_seconds))
		timeline_status.text = "Keyframe movido."
		_refresh_timeline_tracks()
	else:
		timeline_status.text = engine.last_error


func _delete_manual_keyframe() -> void:
	if scene_parser == null or timeline_target_option.item_count == 0:
		return
	var target_id := String(timeline_target_option.get_item_metadata(timeline_target_option.selected))
	var property_name: String = String(["position", "rotation_degrees", "scale"][timeline_property_option.selected])
	var engine = scene_parser.timeline_engine
	if engine.delete_keyframe(target_id, property_name, timeline_time_spin.value):
		timeline_slider.max_value = maxf(0.01, float(engine.duration_seconds))
		timeline_status.text = "Keyframe eliminado."
		_refresh_timeline_tracks()
	else:
		timeline_status.text = engine.last_error


func _seek_timeline(value: float) -> void:
	if scene_parser != null:
		scene_parser.seek_scene(value)
		if timeline_time_spin != null:
			timeline_time_spin.set_value_no_signal(value)
		_sync_timeline_values()


func _play_timeline() -> void:
	if scene_parser != null:
		scene_parser.play_scene()


func _pause_timeline() -> void:
	if scene_parser != null:
		scene_parser.pause_scene()


func _stop_timeline() -> void:
	if scene_parser != null:
		scene_parser.stop_scene()
		if timeline_slider != null:
			timeline_slider.set_value_no_signal(0.0)
		if timeline_time_spin != null:
			timeline_time_spin.set_value_no_signal(0.0)


func _save_project() -> void:
	if scene_parser == null or scene_parser.timeline_engine == null:
		return
	var saved := ProjectStoreScript.save_project("current", "Proyecto JEDL", scene_parser.scene_data, scene_parser.timeline_engine.to_dictionary())
	json_status.text = "Proyecto guardado en user://projects/current.json" if saved else "No se pudo guardar el proyecto."


func _open_saved_project() -> void:
	if scene_parser == null:
		return
	var data := ProjectStoreScript.load_project("current")
	if data.is_empty():
		json_status.text = "No existe un proyecto guardado compatible."
		return
	if not scene_parser.load_scene_text(JSON.stringify(data["scene"])):
		json_status.text = scene_parser.last_error
		return
	if not scene_parser.timeline_engine.load_dictionary(data["timeline"]):
		json_status.text = scene_parser.timeline_engine.last_error
		return
	json_editor.text = JSON.stringify(data["scene"], "\t")
	_refresh_timeline_targets()
	json_status.text = "Proyecto recuperado correctamente."


func _restore_project() -> void:
	if scene_parser == null:
		return
	var data := ProjectStoreScript.restore_project("current")
	if data.is_empty():
		json_status.text = "No existe una copia anterior para restaurar."
		return
	if not scene_parser.load_scene_text(JSON.stringify(data["scene"])):
		json_status.text = scene_parser.last_error
		return
	if not scene_parser.timeline_engine.load_dictionary(data["timeline"]):
		json_status.text = scene_parser.timeline_engine.last_error
		return
	json_editor.text = JSON.stringify(data["scene"], "\t")
	_refresh_timeline_targets()
	json_status.text = "Versión anterior restaurada."


func _duplicate_project() -> void:
	var duplicated := ProjectStoreScript.duplicate_project("current", "currentcopy", "Copia de JEDL Studio")
	json_status.text = "Proyecto duplicado como currentcopy." if duplicated else "Guarda primero el proyecto o elimina la copia existente."


func _blank_scene_document() -> Dictionary:
	return {
		"version": 2,
		"title": "Proyecto nuevo",
		"characters": [],
		"objects": [],
		"elements": [],
		"subtitles": [],
		"sounds": [],
		"actions": []
	}
