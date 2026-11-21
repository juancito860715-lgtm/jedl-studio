extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var world := Node3D.new()
    root.add_child(world)
    var subtitle := Label.new()
    root.add_child(subtitle)
    var audio := AudioStreamPlayer.new()
    root.add_child(audio)
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    parser.subtitle_label = subtitle
    parser.audio_player = audio

    var loaded: bool = parser.load_scene_file("res://scenes/scene.example.json")
    assert(loaded, "Example scene JSON must load")
    assert(parser.scene_data.has("characters"), "Characters array must exist")
    assert(parser.active_instances.size() == 1, "Exactly one sample character must instantiate")
    assert(parser._events.size() == 4, "Two subtitles must create four timeline events")
    assert(parser._events[0]["kind"] == "subtitle", "Timeline must be sorted by time")

    parser.play_scene()
    assert(parser._playing, "Playback must start")
    parser._process(0.25)
    assert(subtitle.text == "JEDL Studio: escena 3D cargada desde JSON", "First subtitle must appear at 0.25s")
    parser._process(2.8)
    assert(subtitle.text == "", "Subtitle must clear after its duration")

    parser.stop_scene()
    parser.queue_free()
    world.queue_free()
    subtitle.queue_free()
    audio.queue_free()
    print("SCENE_PARSER_TEST_OK")
    quit(0)
