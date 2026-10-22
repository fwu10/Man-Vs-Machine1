extends Control
## Robot select for Versus (player 2 picks) and Training (sparring partner).

var idx := 0
var _actor: MenuActor
var _t := 0.0
var _stage_holder: Node2D


func _ready() -> void:
	theme = Game.theme
	Audio.play_music("menu")
	_stage_holder = Node2D.new()
	add_child(_stage_holder)
	move_child(_stage_holder, 0)
	_actor = MenuActor.new()
	_actor.position = Vector2(470, 300)
	add_child(_actor)
	_refresh()


func _refresh() -> void:
	var cid: String = Game.ROSTER[idx]
	for c in _stage_holder.get_children():
		c.queue_free()
	var st: Node2D = load("res://scenes/stages/%s.tscn" % Game.STAGE_FOR[cid]).instantiate()
	_stage_holder.add_child(st)
	_actor.setup(Game.get_character(cid), "intro", true)
	queue_redraw()


func _process(delta: float) -> void:
	_t += delta
	if _actor.anim == "intro" and _t > 0.8:
		_actor.play("idle")
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	var left := event.is_action_pressed("ui_left") or event.is_action_pressed("p1_left") or event.is_action_pressed("p2_left")
	var right := event.is_action_pressed("ui_right") or event.is_action_pressed("p1_right") or event.is_action_pressed("p2_right")
	if left or right:
		idx = (idx + (1 if right else -1) + Game.ROSTER.size()) % Game.ROSTER.size()
		_t = 0.0
		Audio.play_sfx("menu_move")
		_refresh()
	elif event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_lp") or event.is_action_pressed("p2_lp"):
		Audio.play_sfx("menu_select")
		var cid: String = Game.ROSTER[idx]
		if Game.mode == "training":
			Game.start_training(cid)
		else:
			Game.start_versus(cid)
	elif event.is_action_pressed("ui_cancel"):
		Audio.play_sfx("menu_back")
		Game.to_menu()


func _draw() -> void:
	var cid: String = Game.ROSTER[idx]
	var d := Game.get_character(cid)
	draw_rect(Rect2(0, 0, 640, 46), Color(0, 0, 0, 0.7))
	var head := "PLAYER 2 - CHOOSE YOUR MACHINE" if Game.mode == "versus" else "TRAINING - CHOOSE A SPARRING PARTNER"
	PixelText.draw(self, Vector2(320, 30), head, 2, Color(1, 0.85, 0.3), Color.BLACK, true)
	# roster strip
	for i in Game.ROSTER.size():
		var c := Game.get_character(Game.ROSTER[i])
		var r := Rect2(22 + i * 58, 60, 52, 48)
		draw_rect(r.grow(2), Color(1, 0.8, 0.2) if i == idx else Color(0.2, 0.2, 0.28))
		draw_rect(r, c.theme_color.darkened(0.75))
		if c.portrait:
			draw_texture_rect_region(c.portrait, r, Rect2(Vector2.ZERO, c.portrait.get_size()))
	# info card
	draw_rect(Rect2(16, 122, 300, 170), Color(0, 0, 0, 0.65))
	draw_rect(Rect2(16, 122, 300, 170), d.theme_color, false, 1)
	PixelText.draw(self, Vector2(26, 150), d.display_name, 3, d.theme_color.lightened(0.3))
	PixelText.draw(self, Vector2(26, 166), d.title, 1, Color(0.9, 0.9, 1))
	var lines := _wrap(d.bio, 46)
	for i in lines.size():
		PixelText.draw(self, Vector2(26, 184 + i * 11), lines[i], 1, Color(0.75, 0.78, 0.85), Color(0, 0, 0, 0))
	PixelText.draw(self, Vector2(26, 240), "HEALTH %d   SPEED %.1f" % [d.max_health, d.walk_fwd], 1, Color(0.6, 0.95, 1))
	PixelText.draw(self, Vector2(26, 254), "STAGE: " + Game.STAGE_NAMES[Game.STAGE_FOR[cid]], 1, Color(0.6, 0.95, 1))
	PixelText.draw(self, Vector2(26, 280), "< > SELECT   ENTER/J CONFIRM   ESC BACK", 1, Color(1, 0.85, 0.4))


static func _wrap(text: String, width: int) -> Array[String]:
	var out: Array[String] = []
	var line := ""
	for w in text.split(" "):
		if (line + " " + w).length() > width:
			out.append(line)
			line = w
		else:
			line = w if line == "" else line + " " + w
	if line != "":
		out.append(line)
	return out
