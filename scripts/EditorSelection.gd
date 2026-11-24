extends RefCounted
class_name JEDLEditorSelection

# Selección geométrica sin física ni dependencias de escena.
# Cada elemento contiene id, position, size, scale, rotation, offset,
# z_index, draw_order y opcionalmente polygon (vértices locales).

static func select_element(items: Array, point: Vector2) -> String:
	var selected_id := ""
	var best_z := -2147483648
	var best_order := -1
	for index in range(items.size()):
		var value: Variant = items[index]
		if not (value is Dictionary):
			continue
		var item: Dictionary = value
		if not _contains_point(item, point):
			continue
		var z_value := int(item.get("z_index", 0))
		var order_value := int(item.get("draw_order", index))
		if z_value > best_z or (z_value == best_z and order_value >= best_order):
			best_z = z_value
			best_order = order_value
			selected_id = String(item.get("id", ""))
	return selected_id


static func _contains_point(item: Dictionary, point: Vector2) -> bool:
	var position_value: Vector2 = item.get("position", Vector2.ZERO)
	var scale_value: Vector2 = item.get("scale", Vector2.ONE)
	if is_zero_approx(scale_value.x) or is_zero_approx(scale_value.y):
		return false
	var rotation_value := float(item.get("rotation", 0.0))
	var local_point := (point - position_value).rotated(-rotation_value)
	local_point = Vector2(local_point.x / scale_value.x, local_point.y / scale_value.y)
	var polygon: Variant = item.get("polygon", null)
	if polygon is Array or polygon is PackedVector2Array:
		if polygon.size() >= 3:
			return _point_in_polygon(local_point, polygon)
	var size_value: Vector2 = item.get("size", Vector2.ZERO)
	if size_value.x <= 0.0 or size_value.y <= 0.0:
		return false
	var offset_value: Vector2 = item.get("offset", Vector2.ZERO)
	return Rect2(offset_value - size_value * 0.5, size_value).has_point(local_point)


static func _point_in_polygon(point: Vector2, vertices: Variant) -> bool:
	var inside := false
	var previous: int = vertices.size() - 1
	for current in range(vertices.size()):
		var a: Vector2 = vertices[current]
		var b: Vector2 = vertices[previous]
		if (a.y > point.y) != (b.y > point.y):
			var crossing_x: float = (b.x - a.x) * (point.y - a.y) / (b.y - a.y) + a.x
			if point.x < crossing_x:
				inside = not inside
		previous = current
	return inside
