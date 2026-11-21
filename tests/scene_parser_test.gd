extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_tests")


func _run_tests() -> void:
    var world := Node3D.new()
    root.add_child(world)
    var subtitles := RichTextLabel.new()
    root.add_child(subtitles)
    var audio := AudioStreamPlayer.new()
    root.add_child(audio)
    var parser = SceneParserScript.new()
    root.add_child(parser)
    parser.world_root = world
    parser.subtitle_label = subtitles
    parser.audio_player = audio

    var loaded: bool = parser.load_scene_file("res://scenes/scene.example.json")
    assert(loaded, "Example scene JSON must load")
    assert(parser.scene_data.has("characters"), "Scene data must include characters")
    assert(parser.active_instances.size() == 1, "The sample character must instantiate")
    assert(parser._events.size() == 4, "Two subtitles must create four timeline events")

    parser.play_scene()
    assert(parser._playing, "Playback must start")
    assert(subtitles.text == "JEDL Studio: escena 3D cargada desde JSON", "First subtitle must appear at time zero processing")

    print("GODOT_SCENE_PARSER_TEST_OK")
    quit(0)
