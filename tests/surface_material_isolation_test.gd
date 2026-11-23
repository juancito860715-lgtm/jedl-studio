extends SceneTree

const ProductionEditorScript = preload("res://scripts/ProductionEditor.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


var _failure_count := 0


func _run_tests() -> void:
    _test_single_surface_material_isolation()
    _test_multisurface_instance_isolation()
    _test_shader_material_parameter_isolation()
    if _failure_count == 0:
        print("SURFACE_MATERIAL_ISOLATION_TEST_OK")
        quit(0)
    push_error("SURFACE_MATERIAL_ISOLATION_TEST_FAILED: %d check(s)" % _failure_count)
    quit(1)


func _check(condition: bool, message: String) -> void:
    if not condition:
        _failure_count += 1
        push_error("ASSERTION FAILED: " + message)


func _make_triangle_mesh(materials: Array[Material]) -> ArrayMesh:
    var mesh := ArrayMesh.new()
    for material in materials:
        var arrays: Array = []
        arrays.resize(Mesh.ARRAY_MAX)
        arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0)
        ])
        arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2])
        mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
        mesh.surface_set_material(mesh.get_surface_count() - 1, material)
    return mesh


func _make_standard_material(color: Color) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.roughness = 0.62
    material.metallic = 0.18
    material.emission_enabled = true
    material.emission = Color(0.08, 0.12, 0.16, 1.0)
    material.normal_enabled = true
    material.normal_texture = GradientTexture2D.new()
    return material


func _make_shader_material() -> ShaderMaterial:
    var shader := Shader.new()
    shader.code = """
shader_type spatial;
uniform vec4 albedo_color : source_color = vec4(0.8, 0.7, 0.6, 1.0);
uniform sampler2D normal_texture : hint_normal;
uniform float roughness = 0.42;
uniform float metallic = 0.23;
uniform float detail_strength = 0.75;
void fragment() {
    ALBEDO = albedo_color.rgb;
    ROUGHNESS = roughness;
    METALLIC = metallic;
}
"""
    var material := ShaderMaterial.new()
    material.shader = shader
    material.set_shader_parameter("albedo_color", Color(0.8, 0.7, 0.6, 1.0))
    material.set_shader_parameter("roughness", 0.42)
    material.set_shader_parameter("metallic", 0.23)
    material.set_shader_parameter("detail_strength", 0.75)
    return material


func _make_editor() -> ProductionEditor:
    var editor: ProductionEditor = ProductionEditorScript.new()
    root.add_child(editor)
    return editor


func _test_single_surface_material_isolation() -> void:
    var source := _make_standard_material(Color(0.3, 0.4, 0.5, 1.0))
    var mesh_resource := _make_triangle_mesh([source])
    var instance := MeshInstance3D.new()
    instance.mesh = mesh_resource
    root.add_child(instance)

    var editor := _make_editor()
    var edited: Material = editor.ensure_unique_surface_material(instance, 0)
    _check(edited is StandardMaterial3D, "Single-surface mesh must receive an editable StandardMaterial3D")
    _check(instance.get_surface_override_material(0) == edited, "Edited material must be assigned as a per-surface override")
    _check(edited != source, "Edited material must not be the shared source resource")

    var standard := edited as StandardMaterial3D
    var replacement_normal := GradientTexture2D.new()
    _check(editor.set_surface_albedo(instance, 0, Color(0.9, 0.2, 0.1, 1.0)), "Albedo edit must succeed")
    _check(editor.set_surface_normal_map(instance, 0, replacement_normal), "Normal map edit must succeed")
    _check(editor.set_surface_roughness(instance, 0, 0.31), "Roughness edit must succeed")
    _check(editor.set_surface_metallic(instance, 0, 0.77), "Metallic edit must succeed")

    _check(standard.albedo_color == Color(0.9, 0.2, 0.1, 1.0), "Albedo must update on the unique material")
    _check(standard.normal_texture == replacement_normal and standard.normal_enabled, "Normal map must update")
    _check(is_equal_approx(standard.roughness, 0.31), "Roughness must update")
    _check(is_equal_approx(standard.metallic, 0.77), "Metallic must update")
    _check(standard.emission_enabled and standard.emission == Color(0.08, 0.12, 0.16, 1.0),
        "Editing PBR channels must preserve unrelated emission settings")
    _check(source.albedo_color == Color(0.3, 0.4, 0.5, 1.0), "Source material must remain unchanged")
    _check(is_equal_approx(source.roughness, 0.62) and is_equal_approx(source.metallic, 0.18),
        "Source PBR values must remain unchanged")

    editor.queue_free()
    instance.queue_free()


func _test_multisurface_instance_isolation() -> void:
    var first_source := _make_standard_material(Color(0.2, 0.3, 0.4, 1.0))
    var second_source := _make_standard_material(Color(0.6, 0.5, 0.4, 1.0))
    var shared_mesh := _make_triangle_mesh([first_source, second_source])

    var edited_instance := MeshInstance3D.new()
    edited_instance.mesh = shared_mesh
    root.add_child(edited_instance)
    var sibling_instance := MeshInstance3D.new()
    sibling_instance.mesh = shared_mesh
    root.add_child(sibling_instance)

    var editor := _make_editor()
    var edited: Material = editor.ensure_unique_surface_material(edited_instance, 1)
    _check(edited is StandardMaterial3D, "Multi-surface target must retain its material type")
    _check(edited_instance.get_surface_override_material(1) == edited, "Only selected surface receives the override")
    _check(edited_instance.get_surface_override_material(0) == null, "Other surface must not receive an override")
    _check(sibling_instance.get_surface_override_material(1) == null, "Sibling instance must not receive an override")

    _check(editor.set_surface_albedo(edited_instance, 1, Color(0.95, 0.85, 0.1, 1.0)), "Multi-surface albedo edit must succeed")
    _check(editor.set_surface_roughness(edited_instance, 1, 0.12), "Multi-surface roughness edit must succeed")
    var edited_standard := edited as StandardMaterial3D
    _check(edited_standard.albedo_color == Color(0.95, 0.85, 0.1, 1.0), "Selected surface color must update")
    _check(is_equal_approx(edited_standard.roughness, 0.12), "Selected surface roughness must update")
    _check(first_source.albedo_color == Color(0.2, 0.3, 0.4, 1.0), "Unselected surface source must remain unchanged")
    _check(second_source.albedo_color == Color(0.6, 0.5, 0.4, 1.0), "Selected source material must remain unchanged")
    _check(sibling_instance.get_active_material(1) == second_source, "Sibling instance must continue using original material")
    _check(edited_instance.get_active_material(0) == first_source, "Unedited surface must continue using original material")

    editor.queue_free()
    edited_instance.queue_free()
    sibling_instance.queue_free()


func _test_shader_material_parameter_isolation() -> void:
    var source := _make_shader_material()
    var shared_mesh := _make_triangle_mesh([source])
    var edited_instance := MeshInstance3D.new()
    edited_instance.mesh = shared_mesh
    root.add_child(edited_instance)
    var sibling_instance := MeshInstance3D.new()
    sibling_instance.mesh = shared_mesh
    root.add_child(sibling_instance)

    var editor := _make_editor()
    var edited: Material = editor.ensure_unique_surface_material(edited_instance, 0)
    _check(edited is ShaderMaterial, "ShaderMaterial must remain a ShaderMaterial after duplication")
    _check(edited != source, "ShaderMaterial must be duplicated before editing")

    var replacement_normal := GradientTexture2D.new()
    _check(editor.set_surface_albedo(edited_instance, 0, Color(0.1, 0.8, 0.3, 1.0)), "Shader albedo parameter edit must succeed")
    _check(editor.set_surface_normal_map(edited_instance, 0, replacement_normal), "Shader normal parameter edit must succeed")
    _check(editor.set_surface_roughness(edited_instance, 0, 0.27), "Shader roughness parameter edit must succeed")
    _check(editor.set_surface_metallic(edited_instance, 0, 0.81), "Shader metallic parameter edit must succeed")

    var shader_material := edited as ShaderMaterial
    _check(shader_material.get_shader_parameter("albedo_color") == Color(0.1, 0.8, 0.3, 1.0), "Shader albedo parameter must update")
    _check(shader_material.get_shader_parameter("normal_texture") == replacement_normal, "Shader normal parameter must update")
    _check(is_equal_approx(shader_material.get_shader_parameter("roughness"), 0.27), "Shader roughness parameter must update")
    _check(is_equal_approx(shader_material.get_shader_parameter("metallic"), 0.81), "Shader metallic parameter must update")
    _check(is_equal_approx(shader_material.get_shader_parameter("detail_strength"), 0.75),
        "Unrelated shader parameter must be preserved")
    _check(source.get_shader_parameter("albedo_color") == Color(0.8, 0.7, 0.6, 1.0),
        "Shared ShaderMaterial parameters must remain unchanged")
    _check(is_equal_approx(source.get_shader_parameter("roughness"), 0.42), "Shared shader roughness must remain unchanged")
    _check(sibling_instance.get_active_material(0) == source, "Sibling instance must continue using the original ShaderMaterial")

    editor.queue_free()
    edited_instance.queue_free()
    sibling_instance.queue_free()
