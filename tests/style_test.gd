extends SceneTree

const StyleScript = preload("res://scripts/SceneStyleManager.gd")

func _initialize() -> void:
	var actor := Node2D.new()
	var sprite := Sprite2D.new()
	actor.add_child(sprite)
	actor.modulate = Color(0.8,0.6,0.4,0.9)
	sprite.modulate = Color(0.4,0.8,0.6,0.7)
	var nodes:Array = [actor,sprite]
	var originals := StyleScript.capture_originals(nodes)
	var catalog_snapshot := {"assetId":"2d.star_token.v1","path":"res://assets/gallery/2d/star_token.png","tint":"#FFFFFF"}
	var catalog_before := catalog_snapshot.duplicate(true)
	assert(StyleScript.apply_style(nodes,{"id":"cartoon","tint":"#FFCCAA","saturation":0.5}), "global style must apply")
	assert(actor.modulate != Color(0.8,0.6,0.4,0.9), "style must change actor modulate")
	assert(StyleScript.remove_style(nodes,originals), "style removal must succeed")
	assert(actor.modulate == Color(0.8,0.6,0.4,0.9), "actor modulate must restore exactly")
	assert(sprite.modulate == Color(0.4,0.8,0.6,0.7), "sprite modulate must restore exactly")
	assert(catalog_snapshot == catalog_before, "scene style must not mutate catalog records")
	print("STYLE_TEST_OK")
	quit(0)
