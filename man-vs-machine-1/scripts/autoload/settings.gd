extends Node
## Persistent options and high scores (user://settings.cfg).

const PATH := "user://settings.cfg"
const ROUND_TIMES := [45, 60, 99, 0]          ## 0 = infinite
const DIFFICULTY_NAMES := ["EASY", "NORMAL", "HARD"]

var master_volume := 0.8
var music_volume := 0.6
var sfx_volume := 0.8
var round_time := 60
var rounds_to_win := 2
var difficulty := 1
var show_hitboxes := false
var fullscreen := false
var high_score := 0
var best_clear_time := 0.0


func _ready() -> void:
	load_settings()
	apply()


func load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) != OK:
		return
	master_volume = cfg.get_value("audio", "master", master_volume)
	music_volume = cfg.get_value("audio", "music", music_volume)
	sfx_volume = cfg.get_value("audio", "sfx", sfx_volume)
	round_time = cfg.get_value("game", "round_time", round_time)
	rounds_to_win = cfg.get_value("game", "rounds_to_win", rounds_to_win)
	difficulty = cfg.get_value("game", "difficulty", difficulty)
	show_hitboxes = cfg.get_value("debug", "show_hitboxes", show_hitboxes)
	fullscreen = cfg.get_value("video", "fullscreen", fullscreen)
	high_score = cfg.get_value("records", "high_score", high_score)


func save_settings() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("audio", "master", master_volume)
	cfg.set_value("audio", "music", music_volume)
	cfg.set_value("audio", "sfx", sfx_volume)
	cfg.set_value("game", "round_time", round_time)
	cfg.set_value("game", "rounds_to_win", rounds_to_win)
	cfg.set_value("game", "difficulty", difficulty)
	cfg.set_value("debug", "show_hitboxes", show_hitboxes)
	cfg.set_value("video", "fullscreen", fullscreen)
	cfg.set_value("records", "high_score", high_score)
	cfg.save(PATH)


func apply() -> void:
	_set_bus("Master", master_volume)
	_set_bus("Music", music_volume)
	_set_bus("SFX", sfx_volume)
	if DisplayServer.get_name() != "headless":
		var mode := DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED
		if DisplayServer.window_get_mode() != mode:
			DisplayServer.window_set_mode(mode)


func submit_score(score: int) -> bool:
	if score > high_score:
		high_score = score
		save_settings()
		return true
	return false


func _set_bus(bus_name: String, v: float) -> void:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx < 0:
		return
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(v, 0.0001)))
	AudioServer.set_bus_mute(idx, v <= 0.001)
