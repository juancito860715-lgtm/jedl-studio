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

    var loaded: bool = parser.load_scene_file("res://scenes/scene.example.json")
    assert(loaded, "Example scene JSON must load")
    assert(parser.scene_data.has("characters"), "Characters array must exist")
    assert(parser.active_instances.size() == 1, "Exactly one sample character must instantiate")
    assert(parser.active_instances[0].get_meta("jedl_asset_id") == "character.fox.khronos.v1", "Character must resolve from its stable assetId")
    assert(parser.background_sprite != null, "The example scene background must be instantiated behind the 3D character")
    assert(parser.background_sprite.get_meta("jedl_asset_id") == "background.mossy_forest", "Background must resolve from its stable assetId")
    assert(parser.background_sprite.get_parent() == camera, "The background must follow the camera, not cover the world as a CanvasLayer")
    assert(is_equal_approx(parser.background_sprite.position.z, -80.0), "The background must remain at a fixed far depth behind the 3D character")
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
    parser.queue_free()
    world.queue_free()
    camera.queue_free()
    subtitle.queue_free()
    audio.queue_free()
    manager.queue_free()
    print("SCENE_PARSER_TEST_OK")
    quit(0)
