extends Node
## Global game flow: mode, arcade ladder progress, character data cache,
## the shared pixel font/theme and fade transitions between scenes.

const LADDER: Array[String] = ["spark", "bulwark", "volt", "razor", "overlord"]
const ROSTER: Array[String] = ["spark", "bulwark", "volt", "razor", "overlord"]
const STAGE_FOR := {
	"spark": "industrial_arena", "bulwark": "industrial_arena",
	"volt": "neon_foundry", "razor": "neon_foundry", "overlord": "machine_core",
}
const MUSIC_FOR_STAGE := {
	"industrial_arena": "fight_industrial", "neon_foundry": "fight_foundry", "machine_core": "fight_boss",
}
const STAGE_NAMES := {
	"industrial_arena": "INDUSTRIAL ARENA", "neon_foundry": "NEON FOUNDRY", "machine_core": "MACHINE CORE",
}
const PLAYER_ID := "boxer"

const SCENE_MENU := "res://scenes/menus/main_menu.tscn"
const SCENE_FIGHT := "res://scenes/fighting/fight.tscn"
const SCENE_VS := "res://scenes/menus/vs_screen.tscn"
const SCENE_SELECT := "res://scenes/menus/character_select.tscn"
const SCENE_ENDING := "res://scenes/menus/ending.tscn"

var mode := "arcade"              ## arcade / versus / training
var ladder_index := 0
var score := 0
var run_time := 0.0
var opponent_id := "spark"
var stage_id := "industrial_arena"
var p2_human := false             ## versus mode: robot controlled by player 2
var demo := false                 ## attract mode: CPU vs CPU, any key returns to the menu
var font: FontFile
var theme: Theme

var _chars := {}
var _fade: ColorRect
var _fade_layer: CanvasLayer
var _busy := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	font = _build_font()
	theme = _build_theme()
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 100
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_layer.add_child(_fade)


func get_character(cid: String) -> CharacterData:
	if not _chars.has(cid):
		_chars[cid] = CharacterData.load_from(cid)
	return _chars[cid]


# ------------------------------------------------------------------ flow
func start_arcade() -> void:
	demo = false
	mode = "arcade"
	ladder_index = 0
	score = 0
	run_time = 0.0
	p2_human = false
	_setup_ladder_fight()
	goto(SCENE_VS)


func _setup_ladder_fight() -> void:
	opponent_id = LADDER[ladder_index]
	stage_id = STAGE_FOR[opponent_id]


func start_demo() -> void:
	mode = "versus"
	demo = true
	opponent_id = ROSTER[randi() % ROSTER.size()]
	stage_id = STAGE_FOR[opponent_id]
	goto(SCENE_FIGHT)


func start_versus(robot: String) -> void:
	mode = "versus"
	p2_human = true
	opponent_id = robot
	stage_id = STAGE_FOR[robot]
	goto(SCENE_VS)


func start_training(robot: String) -> void:
	mode = "training"
	p2_human = false
	opponent_id = robot
	stage_id = STAGE_FOR[robot]
	goto(SCENE_FIGHT)


## Called by the fight when the match is decided.
func arcade_match_won() -> void:
	ladder_index += 1
	if ladder_index >= LADDER.size():
		Settings.submit_score(score)
		goto(SCENE_ENDING)
	else:
		_setup_ladder_fight()
		goto(SCENE_VS)


func retry_match() -> void:
	goto(SCENE_FIGHT)


func to_menu() -> void:
	demo = false
	get_tree().paused = false
	goto(SCENE_MENU)


## AI difficulty: settings level plus ladder progress (0..~1.2).
func ai_difficulty() -> float:
	var base: float = [0.15, 0.45, 0.8][clampi(Settings.difficulty, 0, 2)]
	if mode == "arcade":
		return base + ladder_index * 0.1
	return base + 0.2


func goto(path: String) -> void:
	if _busy:
		return
	_busy = true
	var t := create_tween()
	t.tween_property(_fade, "color:a", 1.0, 0.25)
	await t.finished
	get_tree().paused = false
	Engine.time_scale = 1.0
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	var t2 := create_tween()
	t2.tween_property(_fade, "color:a", 0.0, 0.3)
	_busy = false


func flash_screen(c: Color, dur := 0.15) -> void:
	_fade.color = c
	var t := create_tween()
	t.tween_property(_fade, "color:a", 0.0, dur)


# ------------------------------------------------------------------ font & theme
## Builds a bitmap FontFile from the generated 6x9 glyph sheet
## (assets/fonts/pixel_font.png, 16 columns, ASCII 32-127).
func _build_font() -> FontFile:
	var f := FontFile.new()
	var path := "res://assets/fonts/pixel_font.png"
	if not ResourceLoader.exists(path):
		return f
	var tex: Texture2D = load(path)
	var img := tex.get_image()
	const CW := 6
	const CH := 9
	var sz := Vector2i(CH, 0)
	f.fixed_size = CH
	f.fixed_size_scale_mode = TextServer.FIXED_SIZE_SCALE_INTEGER_ONLY
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	f.set_texture_image(0, sz, 0, img)
	for code in range(32, 128):
		var idx := code - 32
		var col := idx % 16
		var row := idx / 16
		f.set_glyph_advance(0, CH, code, Vector2(CW, 0))
		f.set_glyph_offset(0, sz, code, Vector2(0, -7))
		f.set_glyph_size(0, sz, code, Vector2(CW, CH))
		f.set_glyph_uv_rect(0, sz, code, Rect2(col * CW, row * CH, CW, CH))
		f.set_glyph_texture_idx(0, sz, code, 0)
	# lowercase letters reuse the uppercase glyphs (arcade style)
	for code in range(97, 123):
		var up := code - 32 - 32
		var col2 := up % 16
		var row2 := up / 16
		f.set_glyph_uv_rect(0, sz, code, Rect2(col2 * CW, row2 * CH, CW, CH))
	f.set_cache_ascent(0, CH, 7)
	f.set_cache_descent(0, CH, 2)
	return f


func _build_theme() -> Theme:
	var t := Theme.new()
	t.default_font = font
	t.default_font_size = 9
	var normal := _box(Color(0.08, 0.09, 0.14, 0.92), Color(0.32, 0.36, 0.48))
	var hover := _box(Color(0.55, 0.12, 0.10, 0.95), Color(1.0, 0.75, 0.3))
	var pressed := _box(Color(0.85, 0.35, 0.1, 1.0), Color(1, 0.95, 0.6))
	for s in ["normal", "disabled"]:
		t.set_stylebox(s, "Button", normal)
	t.set_stylebox("hover", "Button", hover)
	t.set_stylebox("focus", "Button", hover)
	t.set_stylebox("pressed", "Button", pressed)
	t.set_stylebox("hover_pressed", "Button", pressed)
	t.set_color("font_color", "Button", Color(0.86, 0.88, 0.95))
	t.set_color("font_hover_color", "Button", Color(1, 0.95, 0.8))
	t.set_color("font_focus_color", "Button", Color(1, 0.95, 0.8))
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_font_size("font_size", "Button", 18)
	t.set_color("font_color", "Label", Color(0.92, 0.93, 0.98))
	t.set_color("font_shadow_color", "Label", Color(0, 0, 0, 0.85))
	t.set_constant("shadow_offset_x", "Label", 1)
	t.set_constant("shadow_offset_y", "Label", 1)
	t.set_stylebox("panel", "Panel", _box(Color(0.06, 0.06, 0.1, 0.95), Color(0.85, 0.6, 0.2)))
	var sl := _box(Color(0.1, 0.1, 0.16), Color(0.3, 0.32, 0.45))
	t.set_stylebox("slider", "HSlider", sl)
	var fill := StyleBoxFlat.new()
	fill.bg_color = Color(0.9, 0.4, 0.1)
	fill.anti_aliasing = false
	t.set_stylebox("grabber_area", "HSlider", fill)
	t.set_stylebox("grabber_area_highlight", "HSlider", fill)
	return t


func _box(bg: Color, border: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(2)
	s.anti_aliasing = false
	s.content_margin_left = 10
	s.content_margin_right = 10
	s.content_margin_top = 3
	s.content_margin_bottom = 3
	return s
