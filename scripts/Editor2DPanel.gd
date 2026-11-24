extends PanelContainer
class_name Editor2DPanel

signal close_requested

const StyleScript = preload("res://scripts/SceneStyleManager.gd")

var _parser: Variant
var _canvas_root: Node2D
var _selected_node: Node2D
var _position_x: SpinBox
var _position_y: SpinBox
var _rotation: SpinBox
var _scale_x: SpinBox
var _scale_y: SpinBox
var _z_index: SpinBox
var _status: Label
var _style_originals: Dictionary = {}


func configure(parser: Variant, canvas_root: Node2D) -> void:
	_parser = parser
	_canvas_root = canvas_root
	_build_panel()


func set_selected_node(node: Node2D) -> void:
	_selected_node = node
	if _status == null:
		return
	if node == null:
		_status.text = "Sin selección · toca un elemento gráfico 2D"
		return
	_status.text = "Elemento seleccionado: " + node.name
	_position_x.value = node.position.x / 100.0
	_position_y.value = -node.position.y / 100.0
	_rotation.value = node.rotation_degrees
	_scale_x.value = node.scale.x
	_scale_y.value = node.scale.y
	_z_index.value = node.z_index


func _build_panel() -> void:
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(scroll)
	var column := VBoxContainer.new()
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	column.add_theme_constant_override("separation", 8)
	scroll.add_child(column)
	var header := HBoxContainer.new()
	column.add_child(header)
	var title := Label.new()
	title.text = "Editor de elementos 2D auxiliares"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var close := Button.new()
	close.text = "Cerrar"
	close.pressed.connect(func(): close_requested.emit())
	header.add_child(close)
	var explanation := Label.new()
	explanation.text = "Este panel edita imágenes y elementos planos. No crea personajes. Los personajes de JEDL Studio se cargan desde recursos articulados 2.5D o 3D."
	explanation.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(explanation)
	_position_x = _add_spin(column, "Posición X", -100.0, 100.0, 0.05, 0.0)
	_position_y = _add_spin(column, "Posición Y", -100.0, 100.0, 0.05, 0.0)
	_rotation = _add_spin(column, "Rotación", -360.0, 360.0, 1.0, 0.0)
	_scale_x = _add_spin(column, "Escala X", 0.01, 20.0, 0.05, 1.0)
	_scale_y = _add_spin(column, "Escala Y", 0.01, 20.0, 0.05, 1.0)
	_z_index = _add_spin(column, "Orden Z", -128.0, 128.0, 1.0, 0.0)
	var apply_transform := Button.new()
	apply_transform.text = "Aplicar y guardar transformación"
	apply_transform.pressed.connect(_apply_transform)
	column.add_child(apply_transform)
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
	_status.text = "Sin selección · toca un elemento gráfico 2D"
	column.add_child(_status)


func _add_spin(parent: VBoxContainer, label_text: String, minimum: float, maximum: float, step: float, initial: float) -> SpinBox:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var label := Label.new()
	label.text = label_text
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(label)
	var spin := SpinBox.new()
	spin.min_value = minimum
	spin.max_value = maximum
	spin.step = step
	spin.value = initial
	spin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spin)
	return spin


func _apply_transform() -> void:
	if _selected_node == null or not is_instance_valid(_selected_node):
		_status.text = "Selecciona un elemento 2D auxiliar."
		return
	_selected_node.position = Vector2(_position_x.value * 100.0, -_position_y.value * 100.0)
	_selected_node.rotation_degrees = _rotation.value
	_selected_node.scale = Vector2(_scale_x.value, _scale_y.value)
	_selected_node.z_index = int(_z_index.value)
	var entry_id := String(_selected_node.get_meta("jedl_entry_id", _selected_node.name))
	for entry_value in _parser.scene_data.get("elements", []):
		if entry_value is Dictionary and String(entry_value.get("id", "")) == entry_id:
			var position: Array = entry_value.get("position", [0.0, 0.0, 0.0])
			while position.size() < 3:
				position.append(0.0)
			position[0] = _position_x.value
			position[1] = _position_y.value
			entry_value["position"] = position
			entry_value["rotation_degrees"] = [0.0, 0.0, _rotation.value]
			var scale: Array = entry_value.get("scale", [1.0, 1.0, 1.0])
			while scale.size() < 3:
				scale.append(1.0)
			scale[0] = _scale_x.value
			scale[1] = _scale_y.value
			entry_value["scale"] = scale
			entry_value["z_index"] = int(_z_index.value)
			break
	_status.text = "Transformación del elemento aplicada y guardada."


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
	var style := {"id": "cartoon", "tint": "#FFFFFF", "saturation": 0.72}
	_style_originals = StyleScript.capture_originals(nodes)
	StyleScript.apply_style(nodes, style)
	_parser.scene_data["style"] = style.duplicate(true)
	_status.text = "Estilo Cartoon aplicado a los elementos 2D."


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
	_status.text = "Estilo retirado; apariencia original restaurada."
