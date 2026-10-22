extends Node
## Sound effects pool and music player. Missing files are skipped silently so
## audio can never break the game.

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const POOL := 10

var _players: Array[AudioStreamPlayer] = []
var _next := 0
var _cache := {}
var _music: AudioStreamPlayer
var _music_name := ""


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in POOL:
		var p := AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_players.append(p)
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	_music.finished.connect(_on_music_finished)
	add_child(_music)


func _load_stream(path_name: String) -> AudioStream:
	if _cache.has(path_name):
		return _cache[path_name]
	var s: AudioStream = null
	if ResourceLoader.exists(path_name):
		s = load(path_name)
	_cache[path_name] = s
	return s


func play_sfx(sfx_name: String, pitch_jitter := 0.06, volume_db := 0.0) -> void:
	if sfx_name == "":
		return
	var s := _load_stream(SFX_DIR + sfx_name + ".wav")
	if s == null:
		return
	var p := _players[_next]
	_next = (_next + 1) % POOL
	p.stream = s
	p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	p.volume_db = volume_db
	p.play()


func play_music(track: String, restart := false) -> void:
	if track == _music_name and _music.playing and not restart:
		return
	_music_name = track
	var s := _load_stream(MUSIC_DIR + track + ".wav")
	if s == null:
		_music.stop()
		return
	_music.stream = s
	_music.volume_db = 0.0
	_music.play()


func stop_music(fade := 0.6) -> void:
	_music_name = ""
	if not _music.playing:
		return
	var t := create_tween()
	t.tween_property(_music, "volume_db", -40.0, fade)
	t.tween_callback(_music.stop)


func _on_music_finished() -> void:
	if _music_name != "":
		_music.play()   # loop
