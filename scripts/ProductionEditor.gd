extends Node
class_name ProductionEditor

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
    for mesh_instance in meshes:
        var source_material: Material = mesh_instance.material_override
        if source_material == null and mesh_instance.mesh != null and mesh_instance.mesh.get_surface_count() > 0:
            source_material = mesh_instance.get_active_material(0)
        var material: StandardMaterial3D
        if source_material is StandardMaterial3D:
            material = (source_material as StandardMaterial3D).duplicate() as StandardMaterial3D
        else:
            material = StandardMaterial3D.new()
            material.roughness = 0.78
        material.albedo_color = color
        mesh_instance.material_override = material
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
