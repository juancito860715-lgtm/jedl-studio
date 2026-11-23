extends SceneTree

const ProductionEditorScript = preload("res://scripts/ProductionEditor.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var world := Node3D.new()
    root.add_child(world)
    var mesh := MeshInstance3D.new()
    mesh.name = "EditableMesh"
    var shared_source := StandardMaterial3D.new()
    shared_source.albedo_color = Color(0.7, 0.6, 0.5, 1.0)
    var shared_mesh := BoxMesh.new()
    for surface_index in range(shared_mesh.get_surface_count()):
        shared_mesh.surface_set_material(surface_index, shared_source)
    mesh.mesh = shared_mesh
    world.add_child(mesh)

    var sibling_mesh := MeshInstance3D.new()
    sibling_mesh.name = "SiblingMesh"
    sibling_mesh.mesh = shared_mesh
    world.add_child(sibling_mesh)

    var editor = ProductionEditorScript.new()
    root.add_child(editor)
    editor.configure(world)
    assert(editor.select_node(mesh), "Editor must select a valid 3D object")
    assert(editor.set_transform(Vector3(0, 1, 0), Vector3(0, 15, 0), Vector3.ONE),
        "Editor must apply position, rotation and scale")
    assert(mesh.position == Vector3(0, 1, 0), "Position must update")
    assert(is_equal_approx(mesh.rotation_degrees.y, 15.0), "Rotation must update")
    assert(editor.set_material_color(Color(0.2, 0.4, 0.8, 1.0)), "Editor must assign an editable material")
    assert(mesh.material_override is StandardMaterial3D, "Material override must be a StandardMaterial3D")
    assert((mesh.material_override as StandardMaterial3D).albedo_color == Color(0.2, 0.4, 0.8, 1.0),
        "Material color must be applied")
    assert(shared_source.albedo_color == Color(0.7, 0.6, 0.5, 1.0),
        "Legacy color editing must not mutate the shared source material")
    assert(sibling_mesh.material_override == null,
        "Legacy color editing must not assign an override to a sibling instance")
    assert(sibling_mesh.get_active_material(0) == shared_source,
        "Sibling instance must continue using the original shared material")

    assert(editor.add_transform_keyframe(0.0), "Editor must create the first transform keyframe")
    assert(editor.set_transform(Vector3(10, 1, 0), Vector3(0, 45, 0), Vector3.ONE * 1.5),
        "Editor must update the object before the second keyframe")
    assert(editor.add_transform_keyframe(1.0), "Editor must create the second transform keyframe")
    assert(editor.animation_player != null and editor.animation_player.has_animation("JEDL_Editable"),
        "Editable animation must be stored in AnimationPlayer")
    assert(editor.animation_player.has_animation_library(""),
        "Godot 4 default AnimationLibrary must be registered")
    var editable_library: AnimationLibrary = editor.animation_player.get_animation_library("")
    assert(editable_library.has_animation("JEDL_Editable"),
        "Editable animation must be registered inside AnimationLibrary")
    var animation: Animation = editable_library.get_animation("JEDL_Editable")
    assert(animation.get_track_count() == 3, "Timeline must contain position, rotation and scale tracks")
    for track_index in range(3):
        assert(animation.track_get_key_count(track_index) == 2, "Each transform track must contain two keyframes")
    assert(is_equal_approx(editor.get_timeline_length(), 1.05), "Timeline length must include the last keyframe")
    assert(editor.scrub_timeline(0.5), "Timeline must support scrubbing")
    assert(is_equal_approx(mesh.position.x, 5.0), "Scrubbing must evaluate interpolated position")

    assert(not editor.set_transform(Vector3.ZERO, Vector3.ZERO, Vector3(0, 1, 1)),
        "Editor must reject a zero scale")
    editor.queue_free()
    world.queue_free()
    print("PRODUCTION_EDITOR_TEST_OK")
    quit(0)
