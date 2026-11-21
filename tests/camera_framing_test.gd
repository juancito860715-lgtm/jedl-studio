extends SceneTree

const MainScene = preload("res://Main.tscn")


func _initialize() -> void:
    call_deferred("_run_test")


func _run_test() -> void:
    var main := MainScene.instantiate()
    root.add_child(main)
    var distance: float = main._calculate_camera_distance(Vector3(2.0, 4.0, 1.0), 16.0 / 9.0, 55.0)
    assert(distance > 4.0, "Camera distance must fit a character taller than four units")
    var wide_distance: float = main._calculate_camera_distance(Vector3(8.0, 2.0, 1.0), 16.0 / 9.0, 55.0)
    assert(wide_distance > distance, "Wide characters must be framed using horizontal extent")
    var portrait_distance: float = main._calculate_camera_distance(Vector3(2.0, 4.0, 1.0), 9.0 / 16.0, 55.0)
    assert(portrait_distance > distance, "Narrow viewports must fit the character width")
    print("CAMERA_FRAMING_TEST_OK")
    quit(0)
