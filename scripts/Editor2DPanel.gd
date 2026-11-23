extends PanelContainer
class_name Editor2DPanel

signal close_requested
signal character_added
signal character_selected(node: Node2D)

const RigScript = preload("res://scripts/CharacterRig2D.gd")
const StyleScript = preload("res://scripts/SceneStyleManager.gd")

var _parser: Variant
var _canvas_root: Node2D
var _selected_node: Node2D
var _hair_picker: ColorPickerButton
var _shirt_picker: ColorPickerButton
var _appearance_name: LineEdit
var _accessory_id: LineEdit
var _pose_spins: Dictionary = {}
var _pose_time: SpinBox
var _status: Label
var _style_originals: Dictionary = {}


func configure(parser: Variant, canvas_root: Node2D) -> void:
	_parser = parser
	_canvas_root = canvas_root
	_build_panel()


func set_selected_node(node: Node2D) -> void:
	_selected_node = node
	if _status != null:
		_status.text = "Seleccionado: " + node.name if node != null else "Sin selección · toca un elemento del lienzo"


func _build_panel() -> void:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	add_child(column)
	var header := HBoxContainer.new()
	column.add_child(header)
	var title := Label.new()
	title.text = "Editor 2D · personaje, pose y estilo"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var close := Button.new()
	close.text = "Cerrar"
	close.pressed.connect(func(): close_requested.emit())
	header.add_child(close)
	var add_character := Button.new()
	add_character.text = "Añadir personaje 2D"
	add_character.pressed.connect(_add_character)
	column.add_child(add_character)
	_appearance_name = LineEdit.new()
	_appearance_name.text = "Apariencia 1"
	_appearance_name.placeholder_text = "Nombre de apariencia"
	column.add_child(_appearance_name)
	var hair_row := HBoxContainer.new()
	column.add_child(hair_row)
	var hair_label := Label.new()
	hair_label.text = "Cabello"
	hair_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hair_row.add_child(hair_label)
	_hair_picker = ColorPickerButton.new()
	_hair_picker.color = Color("#332211")
	hair_row.add_child(_hair_picker)
	var shirt_row := HBoxContainer.new()
	column.add_child(shirt_row)
	var shirt_label := Label.new()
	shirt_label.text = "Ropa"
	shirt_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	shirt_row.add_child(shirt_label)
	_shirt_picker = ColorPickerButton.new()
	_shirt_picker.color = Color("#3E8B9C")
	shirt_row.add_child(_shirt_picker)
	_accessory_id = LineEdit.new()
	_accessory_id.placeholder_text = "Accesorio (id) · vacío para ninguno"
	column.add_child(_accessory_id)
	var apply_appearance := Button.new()
	apply_appearance.text = "Aplicar y guardar apariencia"
	apply_appearance.pressed.connect(_apply_appearance)
	column.add_child(apply_appearance)
	var pose_heading := Label.new()
	pose_heading.text = "Pose · rotación en grados"
	column.add_child(pose_heading)
	for part_name in RigScript.PART_NAMES:
		var row := HBoxContainer.new()
		column.add_child(row)
		var label := Label.new()
		label.text = part_name
		label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(label)
		var spin := SpinBox.new()
		spin.min_value = -180.0
		spin.max_value = 180.0
		spin.step = 1.0
		spin.value = 0.0
		spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(spin)
		_pose_spins[part_name] = spin
	_pose_time = SpinBox.new()
	_pose_time.min_value = 0.0
	_pose_time.max_value = 600.0
	_pose_time.step = 0.05
	_pose_time.prefix = "Tiempo "
	column.add_child(_pose_time)
	var apply_pose_button := Button.new()
	apply_pose_button.text = "Aplicar pose"
	apply_pose_button.pressed.connect(_apply_pose)
	column.add_child(apply_pose_button)
	var key_pose_button := Button.new()
	key_pose_button.text = "Guardar pose como keyframes"
	key_pose_button.pressed.connect(_save_pose_keyframes)
	column.add_child(key_pose_button)
	var style_button := Button.new()
	style_button.text = "Aplicar estilo Cartoon"
	style_button.pressed.connect(_apply_cartoon_style)
	column.add_child(style_button)
	var remove_style_button := Button.new()
	remove_style_button.text = "Quitar estilo"
	remove_style_button.pressed.connect(_remove_style)
	column.add_child(remove_style_button)
	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.text = "Sin selección · toca un elemento del lienzo"
	column.add_child(_status)


func _add_character() -> void:
	if _parser == null or _canvas_root == null:
		return
	var characters: Array = _parser.scene_data.get("characters_2d", [])
	var next_index := characters.size() + 1
	var entry_id := "character_2d_%02d" % next_index
	var character := RigScript.create_character("Personaje 2D %d" % next_index)
	character.set_meta("jedl_entry_id", entry_id)
	character.set_meta("jedl_asset_id", "character.2d.procedural.v1")
	character.position = Vector2.ZERO
	_canvas_root.add_child(character)
	_parser.active_instances.append(character)
	if _parser.timeline_engine != null:
		_parser.timeline_engine.register_target(entry_id, character)
	if not _parser.scene_data.has("characters_2d") or not (_parser.scene_data["characters_2d"] is Array):
		_parser.scene_data["characters_2d"] = []
	_parser.scene_data["characters_2d"].append({
		"id": entry_id,
		"name": character.name,
		"position": [0.0, 0.0, 0.0],
		"rotation_degrees": [0.0, 0.0, 0.0],
		"scale": [1.0, 1.0, 1.0],
		"proportions": {},
		"appearance": {}
	})
	_selected_node = character
	set_selected_node(character)
	character_selected.emit(character)
	character_added.emit()


func _apply_appearance() -> void:
	if not _is_character_selected():
		_status.text = "Selecciona primero un personaje 2D."
		return
	var appearance := {
		"name": _appearance_name.text.strip_edges() if not _appearance_name.text.strip_edges().is_empty() else "Apariencia",
		"hair_color": _hair_picker.color.to_html(false),
		"shirt_color": _shirt_picker.color.to_html(false),
		"accessory": _accessory_id.text.strip_edges()
	}
	if not RigScript.apply_appearance(_selected_node, appearance):
		_status.text = "No se pudo aplicar la apariencia."
		return
	if not _parser.scene_data.has("appearances") or not (_parser.scene_data["appearances"] is Array):
		_parser.scene_data["appearances"] = []
	var appearances: Array = _parser.scene_data["appearances"]
	if not appearances.has(appearance):
		appearances.append(appearance.duplicate(true))
	var entry := _find_character_entry()
	if not entry.is_empty():
		entry["appearance"] = appearance.duplicate(true)
	_status.text = "Apariencia aplicada y guardada en el documento de escena."


func _apply_pose() -> void:
	if not _is_character_selected():
		_status.text = "Selecciona primero un personaje 2D."
		return
	var pose := _current_pose()
	if RigScript.apply_pose(_selected_node, pose):
		var entry := _find_character_entry()
		if not entry.is_empty():
			entry["pose"] = pose.duplicate(true)
		_status.text = "Pose aplicada."


func _save_pose_keyframes() -> void:
	if not _is_character_selected() or _parser.timeline_engine == null:
		_status.text = "Selecciona un personaje 2D para guardar la pose."
		return
	var entry := _find_character_entry()
	var target_prefix := String(entry.get("id", _selected_node.name))
	var pose := _current_pose()
	if RigScript.add_pose_keyframes(_parser.timeline_engine, target_prefix, _selected_node, _pose_time.value, pose):
		_status.text = "Pose guardada en el Timeline compartido."
	else:
		_status.text = "No se pudieron crear los keyframes de la pose."


func _apply_cartoon_style() -> void:
	if _parser == null:
		return
	var nodes: Array = []
	for instance in _parser.active_instances:
		if instance is CanvasItem:
			nodes.append(instance)
	if nodes.is_empty():
		_status.text = "No hay elementos 2D para estilizar."
		return
	if not _style_originals.is_empty():
		StyleScript.remove_style(nodes, _style_originals)
	var style := {"id":"cartoon","tint":"#FFFFFF","saturation":0.72}
	_style_originals = StyleScript.capture_originals(nodes)
	StyleScript.apply_style(nodes, style)
	_parser.scene_data["style"] = style.duplicate(true)
	_status.text = "Estilo Cartoon aplicado a la escena 2D."


func _remove_style() -> void:
	if _parser == null:
		return
	var nodes: Array = []
	for instance in _parser.active_instances:
		if instance is CanvasItem:
			nodes.append(instance)
	StyleScript.remove_style(nodes, _style_originals)
	_style_originals.clear()
	_parser.scene_data.erase("style")
	_status.text = "Estilo retirado; modulate original restaurado."


func _current_pose() -> Dictionary:
	var pose: Dictionary = {}
	for part_name in RigScript.PART_NAMES:
		var spin := _pose_spins[part_name] as SpinBox
		pose[part_name] = spin.value
	return pose


func _is_character_selected() -> bool:
	return _selected_node != null and is_instance_valid(_selected_node) and bool(_selected_node.get_meta("jedl_character_2d", false))


func _find_character_entry() -> Dictionary:
	if _parser == null:
		return {}
	var entry_id := String(_selected_node.get_meta("jedl_entry_id", _selected_node.name))
	for entry_value in _parser.scene_data.get("characters_2d", []):
		if entry_value is Dictionary and String(entry_value.get("id", "")) == entry_id:
			return entry_value
	return {}

# Panel logic stays in native Godot Controls; all scene data is supplied by SceneParser.
