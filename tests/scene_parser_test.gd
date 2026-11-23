extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")
const CatalogManagerScript = preload("res://scripts/CatalogManager.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var world := Node3D.new()
    root.add_child(world)
    var manager = CatalogManagerScript.new()
    root.add_child(manager)
    assert(manager.load_catalog(), "Root manifest and catalog must validate before scene load")
    var subtitle := Label.new()
    root.add_child(subtitle)
    var audio := AudioStreamPlayer.new()
    root.add_child(audio)
    var camera := Camera3D.new()
    root.add_child(camera)
    camera.current = true
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    parser.catalog_manager = manager
    parser.camera = camera
    parser.subtitle_label = subtitle
    parser.audio_player = audio

    var blank_json := """{"version":2,"characters":[],"objects":[],"elements":[],"subtitles":[],"sounds":[]}"""
    assert(parser.load_scene_text(blank_json), "A blank composition must be a valid starting scene")
    assert(parser.active_instances.is_empty(), "A new blank composition must contain no forced sample character")

    var loaded: bool = parser.load_scene_file("res://scenes/scene.example.json")
    assert(loaded, "Example scene JSON must load")
    assert(parser.scene_data.has("characters"), "Characters array must exist")
    assert(parser.active_instances.size() == 1, "Exactly one sample character must instantiate")
    assert(parser.active_instances[0].get_meta("jedl_asset_id") == "character.fox.khronos.v1", "Character must resolve from its stable assetId")
    assert(not parser.scene_data.has("background"), "The example scene must not contain a photographic background")
    assert(parser._events.size() == 4, "Two subtitles must create four timeline events")
    assert(parser._events[0]["kind"] == "subtitle", "Timeline must be sorted by time")

    var looping_animation := Animation.new()
    parser._configure_animation_loop(looping_animation, true)
    assert(looping_animation.loop_mode == Animation.LOOP_LINEAR, "Walk animation must loop continuously by default")
    parser._configure_animation_loop(looping_animation, false)
    assert(looping_animation.loop_mode == Animation.LOOP_NONE, "One-shot animations must remain supported")
    looping_animation = null

    parser.play_scene()
    assert(parser._playing, "Playback must start")
    parser._process(0.25)
    assert(subtitle.text == "JEDL Studio: escena 3D cargada desde JSON", "First subtitle must appear at 0.25s")
    parser._process(2.8)
    assert(subtitle.text == "", "Subtitle must clear after its duration")

    parser.stop_scene()

    var action_json := """{"version":2,"characters":[{"id":"fox_actor","assetId":"character.fox.khronos.v1","position":[0,0,0]}],"objects":[],"subtitles":[],"sounds":[],"actions":[{"target":"fox_actor","property":"position","time":0.0,"duration":1.0,"to":[10,2,0]},{"target":"fox_actor","property":"rotation_degrees","time":0.0,"duration":2.0,"to":[0,90,0]}]}"""
    assert(parser.load_scene_text(action_json), "JSON transform actions must load and resolve their target by entry id")
    var action_actor := parser.active_instances[0]
    parser.play_scene()
    parser._process(0.5)
    assert(is_equal_approx(action_actor.position.x, 5.0), "Move action must interpolate position at half duration")
    assert(is_equal_approx(action_actor.position.y, 1.0), "Move action must interpolate every vector component")
    assert(is_equal_approx(action_actor.rotation_degrees.y, 22.5), "Rotation action must interpolate independently")
    parser._process(0.5)
    assert(is_equal_approx(action_actor.position.x, 10.0), "Move action must reach its destination at its end time")
    assert(is_equal_approx(action_actor.rotation_degrees.y, 45.0), "Longer concurrent rotation must continue after move ends")
    parser.stop_scene()

    var unknown_target_json := """{"version":2,"characters":[{"id":"fox_actor","assetId":"character.fox.khronos.v1"}],"objects":[],"subtitles":[],"sounds":[],"actions":[{"target":"missing_actor","property":"position","time":0,"duration":1,"to":[1,0,0]}]}"""
    assert(not parser.load_scene_text(unknown_target_json), "Actions targeting missing scene nodes must be rejected")
    assert(parser.last_error.contains("inexistente"), "Missing target rejection must explain the unresolved target")

    var invalid_property_json := """{"version":2,"characters":[{"id":"fox_actor","assetId":"character.fox.khronos.v1"}],"objects":[],"subtitles":[],"sounds":[],"actions":[{"target":"fox_actor","property":"opacity","time":0,"duration":1,"to":[1,1,1]}]}"""
    assert(not parser.load_scene_text(invalid_property_json), "Unsupported action properties must be rejected")

    parser.queue_free()
    world.queue_free()
    camera.queue_free()
    subtitle.queue_free()
    audio.queue_free()
    manager.queue_free()
    print("SCENE_PARSER_TEST_OK")
    quit(0)
