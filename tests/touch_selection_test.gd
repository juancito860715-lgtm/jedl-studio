extends SceneTree

const SelectionScript = preload("res://scripts/EditorSelection.gd")

func _initialize() -> void:
	var items := [
		{"id":"back","position":Vector2(50,50),"size":Vector2(40,40),"scale":Vector2.ONE,"z_index":0,"draw_order":0},
		{"id":"front","position":Vector2(50,50),"size":Vector2(20,20),"scale":Vector2.ONE,"z_index":4,"draw_order":1}
	]
	assert(SelectionScript.select_element(items, Vector2(50,50)) == "front", "overlap must select highest z-index")
	assert(SelectionScript.select_element(items, Vector2(35,50)) == "back", "point inside back bounds must select back item")
	assert(SelectionScript.select_element(items, Vector2(200,200)) == "", "outside tap must deselect")
	var polygon_items := [{"id":"poly","position":Vector2.ZERO,"scale":Vector2.ONE,"rotation":0.0,"polygon":[Vector2(-10,-10),Vector2(10,-10),Vector2(0,10)],"z_index":0,"draw_order":0}]
	assert(SelectionScript.select_element(polygon_items, Vector2(0,0)) == "poly", "polygon interior must be selectable")
	assert(SelectionScript.select_element(polygon_items, Vector2(10,10)) == "", "polygon exterior must not be selectable")
	print("TOUCH_SELECTION_TEST_OK")
	quit(0)
