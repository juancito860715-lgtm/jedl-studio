extends RefCounted
class_name SceneStyleManager

const ORIGINAL_META := "jedl_style_original_modulate"


static func capture_originals(nodes: Array) -> Dictionary:
	var originals: Dictionary = {}
	for node_value in nodes:
		if not (node_value is CanvasItem):
			continue
		var node := node_value as CanvasItem
		var original: Color = node.get_meta(ORIGINAL_META, node.modulate)
		originals[node.get_instance_id()] = original
	return originals


static func apply_style(nodes: Array, style: Dictionary) -> bool:
	if style.is_empty():
		return false
	var tint := Color.from_string(String(style.get("tint", "#FFFFFF")), Color.WHITE)
	var saturation := clampf(float(style.get("saturation", 1.0)), 0.0, 1.0)
	for node_value in nodes:
		if not (node_value is CanvasItem):
			continue
		var node := node_value as CanvasItem
		if not node.has_meta(ORIGINAL_META):
			node.set_meta(ORIGINAL_META, node.modulate)
		var base: Color = node.get_meta(ORIGINAL_META)
		var luminance := base.get_luminance()
		var desaturated := Color(luminance, luminance, luminance, base.a).lerp(base, saturation)
		node.modulate = Color(desaturated.r * tint.r, desaturated.g * tint.g, desaturated.b * tint.b, base.a)
	return true


static func remove_style(nodes: Array, originals: Dictionary) -> bool:
	for node_value in nodes:
		if not (node_value is CanvasItem):
			continue
		var node := node_value as CanvasItem
		var instance_id := node.get_instance_id()
		if originals.has(instance_id):
			node.modulate = originals[instance_id]
		elif node.has_meta(ORIGINAL_META):
			node.modulate = node.get_meta(ORIGINAL_META)
		if node.has_meta(ORIGINAL_META):
			node.remove_meta(ORIGINAL_META)
	return true


static func restore_from_metadata(nodes: Array) -> bool:
	var found := false
	for node_value in nodes:
		if not (node_value is CanvasItem):
			continue
		var node := node_value as CanvasItem
		if node.has_meta(ORIGINAL_META):
			node.modulate = node.get_meta(ORIGINAL_META)
			node.remove_meta(ORIGINAL_META)
			found = true
	return found
