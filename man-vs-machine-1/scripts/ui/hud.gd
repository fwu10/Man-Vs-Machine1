extends CanvasLayer
## Fight HUD: health bars with damage trails, portraits, names, round pips,
## timer, power meters, combo counters and big announcements.

@onready var canvas: Control = $Canvas

var p1: Fighter
var p2: Fighter
var match_node: Node
var shown := [1.0, 1.0]       ## smoothed health ratio
var trail := [1.0, 1.0]       ## delayed red damage trail
var trail_wait := [0, 0]
var wins := [0, 0]
var timer_text := "99"
var combo := [0, 0]
var combo_t := [0, 0]
var announce_text := ""
var announce_color := Color.WHITE
var announce_t := 0
var announce_len := 1
var announce_scale := 4
var announce_blink := false
var super_text := ""
var super_side := 0
var super_t := 0
var training_lines: Array[String] = []
var _frame := 0
var demo := false


func setup(a: Fighter, b: Fighter, m: Node) -> void:
	p1 = a
	p2 = b
	match_node = m
	canvas.draw.connect(_draw_hud)


func reset_round() -> void:
	shown = [1.0, 1.0]
	trail = [1.0, 1.0]
	combo = [0, 0]


func set_wins(w: Array) -> void:
	wins = w.duplicate()


func update_timer(frames: int) -> void:
	timer_text = "--" if frames < 0 else "%02d" % ceili(frames / 60.0)


func show_combo(side: int, hits: int) -> void:
	combo[side] = hits
	combo_t[side] = 70


func announce(text: String, color: Color, frames: int, scale := 4, blink := false) -> void:
	announce_text = text
	announce_color = color
	announce_t = frames
	announce_len = frames
	announce_scale = scale
	announce_blink = blink


func super_flash(side: int, text: String) -> void:
	super_text = text
	super_side = side
	super_t = 50


func training_info(mode_name: String, combo_dmg: float, hits: int) -> void:
	training_lines = [
		"DUMMY: %s  [BACKSPACE]" % mode_name,
		"COMBO DMG: %d  HITS: %d" % [int(combo_dmg), hits],
		"HITBOXES: %s  [F1]" % ("ON" if Settings.show_hitboxes else "OFF"),
	]


func _process(_delta: float) -> void:
	if p1 == null:
		return
	_frame += 1
	for i in 2:
		var f := p1 if i == 0 else p2
		var target := f.health / f.data.max_health
		shown[i] = move_toward(shown[i], target, 0.02)
		if trail[i] > shown[i]:
			trail_wait[i] += 1
			if trail_wait[i] > 30:
				trail[i] = move_toward(trail[i], shown[i], 0.006)
		else:
			trail[i] = shown[i]
			trail_wait[i] = 0
		if combo_t[i] > 0:
			combo_t[i] -= 1
	if announce_t > 0:
		announce_t -= 1
	if super_t > 0:
		super_t -= 1
	canvas.queue_redraw()


func _draw_hud() -> void:
	var c := canvas
	_bar(c, 0, Rect2(48, 10, 234, 12))
	_bar(c, 1, Rect2(358, 10, 234, 12))
	_portrait(c, p1, Rect2(4, 4, 40, 36), false)
	_portrait(c, p2, Rect2(596, 4, 40, 36), true)
	PixelText.draw(c, Vector2(48, 34), p1.data.display_name, 1, Color(1, 0.9, 0.75))
	PixelText.draw(c, Vector2(592 - PixelText.width(p2.data.display_name, 1), 34), p2.data.display_name, 1, Color(0.8, 0.9, 1.0))
	# round pips
	var need: int = Settings.rounds_to_win
	for i in need:
		_pip(c, Vector2(270 - i * 12, 27), i < wins[0])
		_pip(c, Vector2(364 + i * 12, 27), i < wins[1])
	# timer
	c.draw_rect(Rect2(298, 4, 44, 30), Color(0, 0, 0, 0.55))
	c.draw_rect(Rect2(298, 4, 44, 30), Color(0.9, 0.7, 0.2), false, 1)
	var tcol := Color(1, 0.3, 0.2) if timer_text != "--" and int(timer_text) <= 10 and (_frame / 15) % 2 == 0 else Color(1, 0.92, 0.6)
	PixelText.draw(c, Vector2(320, 30), timer_text, 3, tcol, Color.BLACK, true)
	# power meters
	_meter(c, p1, Rect2(10, 344, 110, 7), false)
	_meter(c, p2, Rect2(520, 344, 110, 7), true)
	# combos
	for i in 2:
		if combo_t[i] > 0 and combo[i] >= 2:
			var x := 18.0 if i == 0 else 622.0
			var txt := "%d HITS" % combo[i]
			var pop := 1 if combo_t[i] < 60 else 2
			if i == 1:
				x -= PixelText.width(txt, 2 + (pop - 1))
			PixelText.draw(c, Vector2(x, 86), txt, 2 + (pop - 1), Color(1, 0.85, 0.2))
			PixelText.draw(c, Vector2(x if i == 0 else 622 - PixelText.width("COMBO", 1), 98), "COMBO", 1, Color(1, 0.5, 0.2))
	# super name
	if super_t > 0:
		var sx := 20.0 if super_side == 0 else 620.0 - PixelText.width(super_text, 2)
		c.draw_rect(Rect2(0, 120, 640, 26), Color(0, 0, 0, 0.5))
		PixelText.draw(c, Vector2(sx, 140), super_text, 2, Color(1, 0.9, 0.4))
	# announcement
	if announce_t > 0 and (not announce_blink or (announce_t / 6) % 2 == 0 or announce_t < announce_len - 60):
		var age := announce_len - announce_t
		var s := announce_scale
		if age < 4:
			s = announce_scale + 2
		var y := 170.0 + s * 4
		c.draw_rect(Rect2(0, 170 - s * 6, 640, s * 12), Color(0, 0, 0, 0.35))
		PixelText.draw(c, Vector2(320, y), announce_text, s, announce_color, Color(0.05, 0.02, 0.02), true)
	if demo and (_frame / 30) % 2 == 0:
		PixelText.draw(c, Vector2(320, 330), "DEMO - PRESS ANY KEY", 2, Color(1, 0.9, 0.5), Color.BLACK, true)
	# training panel
	if training_lines.size() > 0:
		c.draw_rect(Rect2(6, 46, 200, 40), Color(0, 0, 0, 0.5))
		for i in training_lines.size():
			PixelText.draw(c, Vector2(10, 58 + i * 11), training_lines[i], 1, Color(0.6, 0.95, 1.0))


func _bar(c: Control, side: int, r: Rect2) -> void:
	c.draw_rect(r.grow(2), Color(0.05, 0.05, 0.08))
	c.draw_rect(r.grow(1), Color(0.75, 0.6, 0.25))
	c.draw_rect(r, Color(0.22, 0.04, 0.05))
	var w_trail: float = r.size.x * trail[side]
	var w: float = r.size.x * shown[side]
	var col := Color(1.0, 0.82, 0.18) if shown[side] > 0.3 else Color(1.0, 0.3, 0.15)
	if side == 0:
		# P1 drains toward the left edge (away from the centre)
		c.draw_rect(Rect2(r.position.x + r.size.x - w_trail, r.position.y, w_trail, r.size.y), Color(0.85, 0.12, 0.1))
		c.draw_rect(Rect2(r.position.x + r.size.x - w, r.position.y, w, r.size.y), col)
		c.draw_rect(Rect2(r.position.x + r.size.x - w, r.position.y, w, 3), col.lightened(0.45))
	else:
		c.draw_rect(Rect2(r.position.x, r.position.y, w_trail, r.size.y), Color(0.85, 0.12, 0.1))
		c.draw_rect(Rect2(r.position.x, r.position.y, w, r.size.y), col)
		c.draw_rect(Rect2(r.position.x, r.position.y, w, 3), col.lightened(0.45))
	c.draw_rect(Rect2(r.position.x, r.end.y - 2, r.size.x, 2), Color(0, 0, 0, 0.25))


func _portrait(c: Control, f: Fighter, r: Rect2, flip: bool) -> void:
	c.draw_rect(r.grow(1), Color(0.75, 0.6, 0.25))
	c.draw_rect(r, f.data.theme_color.darkened(0.7))
	if f.data.portrait:
		var tex := f.data.portrait
		if flip:
			PixelText.draw_flipped(c, tex, r)
		else:
			c.draw_texture_rect_region(tex, r, Rect2(Vector2.ZERO, tex.get_size()))


func _pip(c: Control, p: Vector2, on: bool) -> void:
	c.draw_rect(Rect2(p, Vector2(8, 8)), Color(0.05, 0.05, 0.08))
	c.draw_rect(Rect2(p + Vector2(1, 1), Vector2(6, 6)), Color(1, 0.8, 0.2) if on else Color(0.25, 0.25, 0.3))


func _meter(c: Control, f: Fighter, r: Rect2, flip: bool) -> void:
	c.draw_rect(r.grow(1), Color(0.05, 0.05, 0.08))
	c.draw_rect(r, Color(0.12, 0.12, 0.2))
	var w := r.size.x * f.meter / 100.0
	var full := f.meter >= 100.0
	var col := Color(0.3, 0.7, 1.0) if not full else (Color(1, 1, 1) if (_frame / 5) % 2 == 0 else Color(0.4, 0.9, 1.0))
	if flip:
		c.draw_rect(Rect2(r.end.x - w, r.position.y, w, r.size.y), col)
	else:
		c.draw_rect(Rect2(r.position, Vector2(w, r.size.y)), col)
	var label := "POWER MAX" if full else "POWER"
	var lx := r.position.x if not flip else r.end.x - PixelText.width(label, 1)
	PixelText.draw(c, Vector2(lx, r.position.y - 2), label, 1, Color(0.7, 0.85, 1.0))
