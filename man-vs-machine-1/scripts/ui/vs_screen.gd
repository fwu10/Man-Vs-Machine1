extends Control
## Pre-fight opponent introduction: portraits slide in, the arcade ladder
## shows progress, then the fight loads (auto or on button press).

var _t := 0.0
var _hero: CharacterData
var _foe: CharacterData
var _started := false
var _boss := false


func _ready() -> void:
	theme = Game.theme
	_hero = Game.get_character(Game.PLAYER_ID)
	_foe = Game.get_character(Game.opponent_id)
	_boss = Game.opponent_id == "overlord"
	Audio.play_sfx("alarm" if _boss else "fight")
	Audio.stop_music(0.4)


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()
	if _t > 4.5:
		_go()


func _unhandled_input(event: InputEvent) -> void:
	if _t > 0.8 and (event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_lp")):
		_go()


func _go() -> void:
	if _started:
		return
	_started = true
	Audio.play_sfx("menu_select")
	Game.goto(Game.SCENE_FIGHT)


func _draw() -> void:
	var k := clampf(_t / 0.45, 0.0, 1.0)
	var ease_k := 1.0 - pow(1.0 - k, 3)
	# split background: warm human side, cold machine side
	draw_rect(Rect2(0, 0, 640, 360), Color(0.03, 0.02, 0.04))
	draw_colored_polygon(PackedVector2Array([Vector2(0, 0), Vector2(360, 0), Vector2(280, 360), Vector2(0, 360)]), Color(0.35, 0.07, 0.05))
	draw_colored_polygon(PackedVector2Array([Vector2(360, 0), Vector2(640, 0), Vector2(640, 360), Vector2(280, 360)]),
		Color(0.25, 0.02, 0.03) if _boss else Color(0.05, 0.1, 0.22))
	for i in 24:
		var y := fmod(i * 17.0 + _t * 220.0, 380.0) - 10
		draw_rect(Rect2(0, y, 640, 1), Color(1, 1, 1, 0.04))
	# portraits (2x of the 2x renders)
	var lx := lerpf(-260, 20, ease_k)
	var rx := lerpf(900, 380, ease_k)
	_portrait(_hero, Rect2(lx, 70, 240, 220), false)
	_portrait(_foe, Rect2(rx, 70, 240, 220), true)
	PixelText.draw(self, Vector2(lx + 10, 312), _hero.display_name, 3, Color(1, 0.85, 0.5))
	PixelText.draw(self, Vector2(rx + 230 - PixelText.width(_foe.display_name, 3), 312), _foe.display_name, 3, _foe.theme_color.lightened(0.35))
	PixelText.draw(self, Vector2(rx + 230 - PixelText.width(_foe.title, 1), 326), _foe.title, 1, Color(0.85, 0.9, 1))
	if _t > 0.45:
		var s := 6 if _t < 0.55 else 5
		PixelText.draw(self, Vector2(320, 205), "VS", s, Color(1, 0.9, 0.3), Color(0.3, 0, 0), true)
	# header: mode / ladder progress
	draw_rect(Rect2(0, 0, 640, 40), Color(0, 0, 0, 0.6))
	if Game.mode == "arcade":
		PixelText.draw(self, Vector2(16, 26), "ARCADE  STAGE %d/%d" % [Game.ladder_index + 1, Game.LADDER.size()], 2, Color(1, 0.85, 0.3))
		for i in Game.LADDER.size():
			var c := Game.get_character(Game.LADDER[i])
			var r := Rect2(390 + i * 48, 4, 40, 32)
			draw_rect(r.grow(1), Color(1, 0.8, 0.2) if i == Game.ladder_index else Color(0.3, 0.3, 0.35))
			draw_rect(r, Color(0.1, 0.1, 0.12))
			if c.portrait:
				draw_texture_rect_region(c.portrait, r, Rect2(Vector2.ZERO, c.portrait.get_size()),
					Color(0.35, 0.35, 0.35) if i < Game.ladder_index else Color.WHITE)
			if i < Game.ladder_index:
				draw_line(r.position, r.end, Color(1, 0.2, 0.2), 2)
				draw_line(Vector2(r.end.x, r.position.y), Vector2(r.position.x, r.end.y), Color(1, 0.2, 0.2), 2)
	else:
		PixelText.draw(self, Vector2(16, 26), "VERSUS  P1 VS P2", 2, Color(1, 0.85, 0.3))
	PixelText.draw(self, Vector2(320, 56), "STAGE: " + Game.STAGE_NAMES.get(Game.stage_id, ""), 1, Color(0.8, 0.85, 0.95), Color.BLACK, true)
	if _boss and int(_t * 4) % 2 == 0:
		PixelText.draw(self, Vector2(320, 252), "FINAL BOSS", 3, Color(1, 0.15, 0.1), Color.BLACK, true)
	if _t > 1.0:
		PixelText.draw(self, Vector2(320, 350), "PRESS ENTER", 1, Color(1, 1, 1, 0.5 + 0.5 * sin(_t * 6)), Color.BLACK, true)


func _portrait(d: CharacterData, r: Rect2, flip: bool) -> void:
	draw_rect(r.grow(3), Color(0, 0, 0, 0.6))
	draw_rect(r.grow(2), d.theme_color)
	draw_rect(r, d.theme_color.darkened(0.8))
	if d.portrait:
		if flip:
			PixelText.draw_flipped(self, d.portrait, r)
		else:
			draw_texture_rect_region(d.portrait, r, Rect2(Vector2.ZERO, d.portrait.get_size()))
