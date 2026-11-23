extends SceneTree

func _initialize() -> void:
	var selection_script = load("res://scripts/EditorSelection.gd")
	if not _check(selection_script != null, "EditorSelection.gd must load"):
		return
	var items: Array = [
		{"id":"back","position":Vector2(50,50),"size":Vector2(40,40),"scale":Vector2.ONE,"z_index":0,"draw_order":0},
		{"id":"front","position":Vector2(50,50),"size":Vector2(20,20),"scale":Vector2.ONE,"z_index":4,"draw_order":1}
	]
	if not _check(selection_script.select_element(items, Vector2(50,50)) == "front", "overlap must select highest z-index"):
		return
	if not _check(selection_script.select_element(items, Vector2(35,50)) == "back", "point inside back bounds must select back item"):
		return
	if not _check(selection_script.select_element(items, Vector2(200,200)) == "", "outside tap must deselect"):
		return
	var polygon_items: Array = [{"id":"poly","position":Vector2.ZERO,"scale":Vector2.ONE,"rotation":0.0,"polygon":[Vector2(-10,-10),Vector2(10,-10),Vector2(0,10)],"z_index":0,"draw_order":0}]
	if not _check(selection_script.select_element(polygon_items, Vector2(0,0)) == "poly", "polygon interior must be selectable"):
		return
	if not _check(selection_script.select_element(polygon_items, Vector2(10,10)) == "", "polygon exterior must not be selectable"):
		return
	print("TOUCH_SELECTION_TEST_OK")
	quit(0)


func _check(condition: bool, message: String) -> bool:
	if not condition:
		push_error("TOUCH_SELECTION_TEST_FAILED: " + message)
		quit(1)
		return false
	return true
