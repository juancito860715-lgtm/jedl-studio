extends SceneTree

const SceneParserScript = preload("res://scripts/SceneParser.gd")


func _initialize() -> void:
    call_deferred("_run_smoke_test")


func _run_smoke_test() -> void:
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
    var ok: bool = parser.load_scene_file("res://scenes/scene.example.json")
    assert(ok, "Example JSON should load")
    assert(parser.scene_data.has("characters"), "Scene should expose characters")
    assert(parser.active_instances.size() == 1, "Sample Fox GLB should instantiate")
    assert(parser._events.size() == 4, "Subtitle timeline should contain display and clear events")
    parser.play_scene()
    assert(parser._playing, "Playback should start")
    print("GODOT_SMOKE_OK characters=1 subtitle_events=4")
    quit(0)
