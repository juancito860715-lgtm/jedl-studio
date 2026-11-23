extends Node
class_name ProductionEditor

const UNIQUE_SURFACE_MATERIAL_META := "_jedl_unique_surface_material_ids"

signal selection_changed(node: Node3D)
signal transform_changed(node: Node3D)
signal material_changed(node: Node3D)
signal keyframe_added(node: Node3D, time_seconds: float)

var world_root: Node3D
var selected_node: Node3D
var animation_player: AnimationPlayer
var animation_name := "JEDL_Editable"
var last_error := ""


func configure(root: Node3D) -> void:
    world_root = root


func select_node(node: Node3D) -> bool:
    if node == null or not is_instance_valid(node):
        last_error = "No hay un objeto 3D válido seleccionado."
        return false
    selected_node = node
    selection_changed.emit(selected_node)
    return true


func set_transform(position_value: Vector3, rotation_degrees_value: Vector3, scale_value: Vector3) -> bool:
    if not _has_selection():
        return false
    if scale_value.x <= 0.001 or scale_value.y <= 0.001 or scale_value.z <= 0.001:
        last_error = "La escala debe ser mayor que cero en los tres ejes."
        return false
    selected_node.position = position_value
    selected_node.rotation_degrees = rotation_degrees_value
    selected_node.scale = scale_value
    transform_changed.emit(selected_node)
    return true


func ensure_unique_surface_material(mesh: MeshInstance3D, surface: int) -> Material:
    if mesh == null or not is_instance_valid(mesh):
        last_error = "Se necesita una instancia de malla válida."
        return null
    if mesh.mesh == null:
        last_error = "La instancia no tiene una malla asignada."
        return null
    if surface < 0 or surface >= mesh.mesh.get_surface_count():
        last_error = "El índice de superficie está fuera de los límites de la malla."
        return null

    # Reutilizar el clon que este editor ya aisló para esta instancia/superficie.
    # Así las sucesivas ediciones PBR no reemplazan el material bajo referencias activas.
    var tracked_ids: Dictionary = {}
    if mesh.has_meta(UNIQUE_SURFACE_MATERIAL_META) and mesh.get_meta(UNIQUE_SURFACE_MATERIAL_META) is Dictionary:
        tracked_ids = mesh.get_meta(UNIQUE_SURFACE_MATERIAL_META)
    var current_override: Material = mesh.get_surface_override_material(surface)
    if current_override != null and int(tracked_ids.get(surface, 0)) == current_override.get_instance_id():
        return current_override

    # Resolver el material efectivo respetando la precedencia de Godot:
    # override de superficie, override global de instancia y material de la malla.
    var source_material: Material = current_override
    if source_material == null:
        source_material = mesh.material_override
    if source_material == null:
        source_material = mesh.mesh.surface_get_material(surface)

    if source_material == null:
        source_material = StandardMaterial3D.new()

    var unique_material := source_material.duplicate(true) as Material
    if unique_material == null:
        last_error = "No se pudo duplicar el material de la superficie."
        return null

    mesh.set_surface_override_material(surface, unique_material)
    tracked_ids[surface] = unique_material.get_instance_id()
    mesh.set_meta(UNIQUE_SURFACE_MATERIAL_META, tracked_ids)
    return unique_material


func set_surface_albedo(mesh: MeshInstance3D, surface: int, color: Color) -> bool:
    if not _validate_surface_edit(mesh, surface, "albedo_color", color):
        return false
    var material := ensure_unique_surface_material(mesh, surface)
    if material == null:
        return false
    if material is StandardMaterial3D:
        (material as StandardMaterial3D).albedo_color = color
    elif material is ShaderMaterial:
        if not _set_shader_parameter_if_present(material as ShaderMaterial, "albedo_color", color):
            last_error = "El ShaderMaterial no declara el parámetro uniforme albedo_color."
            return false
    else:
        last_error = "El material no admite edición de albedo mediante este editor."
        return false
    material_changed.emit(mesh)
    return true


func set_surface_normal_map(mesh: MeshInstance3D, surface: int, texture: Texture2D) -> bool:
    if not _validate_surface_edit(mesh, surface, "normal_texture", texture):
        return false
    var material := ensure_unique_surface_material(mesh, surface)
    if material == null:
        return false
    if material is StandardMaterial3D:
        var standard := material as StandardMaterial3D
        standard.normal_texture = texture
        standard.normal_enabled = texture != null
    elif material is ShaderMaterial:
        if not _set_shader_parameter_if_present(material as ShaderMaterial, "normal_texture", texture):
            last_error = "El ShaderMaterial no declara el parámetro uniforme normal_texture."
            return false
    else:
        last_error = "El material no admite edición de mapa normal mediante este editor."
        return false
    material_changed.emit(mesh)
    return true


func set_surface_roughness(mesh: MeshInstance3D, surface: int, value: float) -> bool:
    if not is_finite(value):
        last_error = "La rugosidad debe ser un número finito."
        return false
    if not _validate_surface_edit(mesh, surface, "roughness", value):
        return false
    var material := ensure_unique_surface_material(mesh, surface)
    if material == null:
        return false
    var safe_value := clampf(value, 0.0, 1.0)
    if material is StandardMaterial3D:
        (material as StandardMaterial3D).roughness = safe_value
    elif material is ShaderMaterial:
        if not _set_shader_parameter_if_present(material as ShaderMaterial, "roughness", safe_value):
            last_error = "El ShaderMaterial no declara el parámetro uniforme roughness."
            return false
    else:
        last_error = "El material no admite edición de rugosidad mediante este editor."
        return false
    material_changed.emit(mesh)
    return true


func set_surface_metallic(mesh: MeshInstance3D, surface: int, value: float) -> bool:
    if not is_finite(value):
        last_error = "La metalicidad debe ser un número finito."
        return false
    if not _validate_surface_edit(mesh, surface, "metallic", value):
        return false
    var material := ensure_unique_surface_material(mesh, surface)
    if material == null:
        return false
    var safe_value := clampf(value, 0.0, 1.0)
    if material is StandardMaterial3D:
        (material as StandardMaterial3D).metallic = safe_value
    elif material is ShaderMaterial:
        if not _set_shader_parameter_if_present(material as ShaderMaterial, "metallic", safe_value):
            last_error = "El ShaderMaterial no declara el parámetro uniforme metallic."
            return false
    else:
        last_error = "El material no admite edición de metalicidad mediante este editor."
        return false
    material_changed.emit(mesh)
    return true


func _validate_surface_edit(mesh: MeshInstance3D, surface: int, parameter_name: String, value: Variant) -> bool:
    if mesh == null or not is_instance_valid(mesh) or mesh.mesh == null:
        last_error = "Se necesita una instancia de malla válida."
        return false
    if surface < 0 or surface >= mesh.mesh.get_surface_count():
        last_error = "El índice de superficie está fuera de los límites de la malla."
        return false
    var source_material: Material = mesh.get_surface_override_material(surface)
    if source_material == null:
        source_material = mesh.material_override
    if source_material == null:
        source_material = mesh.mesh.surface_get_material(surface)
    if source_material == null or source_material is StandardMaterial3D:
        return true
    if source_material is ShaderMaterial:
        if _shader_parameter_accepts(source_material as ShaderMaterial, parameter_name, value):
            return true
        last_error = "El ShaderMaterial no declara un uniforme compatible: " + parameter_name
        return false
    last_error = "El material no admite esta edición PBR: " + parameter_name
    return false


func _shader_parameter_accepts(material: ShaderMaterial, parameter_name: String, value: Variant) -> bool:
    if material == null or material.shader == null:
        return false
    for uniform_info in material.shader.get_shader_uniform_list():
        if String(uniform_info.get("name", "")) != parameter_name:
            continue
        var uniform_type := int(uniform_info.get("type", TYPE_NIL))
        var value_type := typeof(value)
        if value == null and uniform_type == TYPE_OBJECT:
            return true
        if value_type == TYPE_COLOR:
            return uniform_type == TYPE_COLOR or uniform_type == TYPE_VECTOR4
        if value_type == TYPE_OBJECT:
            return uniform_type == TYPE_OBJECT
        return uniform_type == value_type
    return false


func _set_shader_parameter_if_present(material: ShaderMaterial, parameter_name: String, value: Variant) -> bool:
    if not _shader_parameter_accepts(material, parameter_name, value):
        return false
    material.set_shader_parameter(parameter_name, value)
    return true


func set_material_color(color: Color) -> bool:
    if not _has_selection():
        return false
    var meshes: Array[MeshInstance3D] = []
    if selected_node is MeshInstance3D:
        meshes.append(selected_node as MeshInstance3D)
    for item in selected_node.find_children("*", "MeshInstance3D", true, false):
        meshes.append(item as MeshInstance3D)
    if meshes.is_empty():
        last_error = "El objeto seleccionado no contiene mallas editables."
        return false

    var edited_mesh_count := 0
    for mesh_instance in meshes:
        if mesh_instance.mesh == null or mesh_instance.mesh.get_surface_count() == 0:
            continue

        # Compatibilidad con la API anterior: el color global del objeto se
        # aplica mediante material_override. Nunca se modifica el material
        # compartido de la malla ni se cambia esta operación por overrides
        # por superficie; esos pertenecen exclusivamente a los setters PBR.
        var source_material: Material = mesh_instance.material_override
        if source_material == null:
            source_material = mesh_instance.mesh.surface_get_material(0)

        var isolated_material: StandardMaterial3D
        if source_material is StandardMaterial3D:
            isolated_material = (source_material.duplicate(true) as StandardMaterial3D)
        else:
            isolated_material = StandardMaterial3D.new()

        if isolated_material == null:
            last_error = "No se pudo crear un material StandardMaterial3D independiente."
            return false

        isolated_material.albedo_color = color
        mesh_instance.material_override = isolated_material
        edited_mesh_count += 1

    if edited_mesh_count == 0:
        last_error = "El objeto seleccionado no contiene superficies editables."
        return false
    material_changed.emit(selected_node)
    return true


func add_transform_keyframe(time_seconds: float) -> bool:
    if not _has_selection():
        return false
    if time_seconds < 0.0:
        last_error = "El tiempo de fotograma clave no puede ser negativo."
        return false
    if world_root == null:
        last_error = "El editor no tiene un nodo raíz de escena."
        return false
    _ensure_animation_player()
    var animation := _get_or_create_editable_animation()
    if animation == null:
        last_error = "No se pudo crear o recuperar la biblioteca de animación editable."
        return false
    var target_path := String(world_root.get_path_to(selected_node))
    _insert_or_update_key(animation, target_path + ":position", time_seconds, selected_node.position)
    _insert_or_update_key(animation, target_path + ":rotation_degrees", time_seconds, selected_node.rotation_degrees)
    _insert_or_update_key(animation, target_path + ":scale", time_seconds, selected_node.scale)
    animation.length = maxf(animation.length, time_seconds + 0.05)
    keyframe_added.emit(selected_node, time_seconds)
    return true


func _insert_or_update_key(animation: Animation, path: String, time_seconds: float, value: Variant) -> void:
    var track := -1
    for index in range(animation.get_track_count()):
        if String(animation.track_get_path(index)) == path:
            track = index
            break
    if track < 0:
        track = animation.add_track(Animation.TYPE_VALUE)
        animation.track_set_path(track, NodePath(path))
        animation.value_track_set_update_mode(track, Animation.UPDATE_CONTINUOUS)
    for key_index in range(animation.track_get_key_count(track) - 1, -1, -1):
        if is_equal_approx(animation.track_get_key_time(track, key_index), time_seconds):
            animation.track_remove_key(track, key_index)
    animation.track_insert_key(track, time_seconds, value)


func scrub_timeline(time_seconds: float) -> bool:
    if animation_player == null or not animation_player.has_animation(animation_name):
        last_error = "Todavía no hay una animación editable."
        return false
    var animation := animation_player.get_animation(animation_name)
    var safe_time := clampf(time_seconds, 0.0, animation.length)
    animation_player.play(animation_name)
    animation_player.seek(safe_time, true)
    animation_player.pause()
    return true


func get_timeline_length() -> float:
    if animation_player == null or not animation_player.has_animation(animation_name):
        return 0.0
    return animation_player.get_animation(animation_name).length


func export_frame(viewport: Viewport, output_path: String) -> bool:
    if viewport == null or output_path.is_empty():
        last_error = "Se necesita un viewport y una ruta de salida."
        return false
    if not output_path.begins_with("user://"):
        last_error = "La exportación debe guardarse dentro de user://."
        return false
    var image := viewport.get_texture().get_image()
    if image == null or image.is_empty():
        last_error = "El viewport todavía no contiene un fotograma renderizado."
        return false
    var error := image.save_png(output_path)
    if error != OK:
        last_error = "No se pudo guardar el fotograma: " + error_string(error)
        return false
    return true


func _ensure_animation_player() -> void:
    if animation_player != null and is_instance_valid(animation_player):
        return
    animation_player = AnimationPlayer.new()
    animation_player.name = "JEDL_Production_AnimationPlayer"
    world_root.add_child(animation_player)
    animation_player.root_node = NodePath("..")


func _get_or_create_editable_animation() -> Animation:
    # Godot 4 almacena animaciones dentro de AnimationLibrary; AnimationPlayer
    # no expone add_animation(). La biblioteca vacía es la biblioteca por defecto.
    if not animation_player.has_animation_library(""):
        animation_player.add_animation_library("", AnimationLibrary.new())
    var library: AnimationLibrary = animation_player.get_animation_library("")
    if library.has_animation(animation_name):
        return library.get_animation(animation_name)

    var animation := Animation.new()
    animation.resource_name = animation_name
    animation.loop_mode = Animation.LOOP_NONE
    var error := library.add_animation(animation_name, animation)
    if error != OK:
        last_error = "No se pudo registrar la animación editable: " + error_string(error)
        return null
    return animation


func _has_selection() -> bool:
    if selected_node == null or not is_instance_valid(selected_node):
        last_error = "Selecciona un objeto 3D antes de editarlo."
        return false
    return true
