extends Node2D
## A fighting stage: parallax background layers generated as pixel art
## (assets/backgrounds/<stage_id>/) plus small procedural animations
## (blinking lights, bobbing crowd, sparks, glowing conduits).
## The fighting floor is at y = 318; nothing here interacts with combat.

@export var stage_id := "industrial_arena"

const LAYERS := [["far", 0.08], ["crowd", 0.12], ["mid", 0.22], ["floor", 0.0]]

var _layers := {}
var _t := 0.0
var _focus := 320.0
var _sparks: Array[Dictionary] = []
var _anim: Node2D


func _ready() -> void:
	for l in LAYERS:
		var path := "res://assets/backgrounds/%s/%s.png" % [stage_id, l[0]]
		if not ResourceLoader.exists(path):
			continue
		var s := Sprite2D.new()
		s.texture = load(path)
		s.centered = false
		add_child(s)
		_layers[l[0]] = [s, l[1]]
		if l[0] == "mid":
			_anim = Node2D.new()
			_anim.draw.connect(_draw_anim)
			add_child(_anim)
	if _anim == null:
		_anim = Node2D.new()
		_anim.draw.connect(_draw_anim)
		add_child(_anim)
	set_focus(320.0)


## Subtle parallax driven by the fighters' midpoint (the arena itself is fixed).
func set_focus(x: float) -> void:
	_focus = lerpf(_focus, x, 0.1)
	for key in _layers:
		var s: Sprite2D = _layers[key][0]
		var k: float = _layers[key][1]
		var w := s.texture.get_width()
		var base := -(w - 640) * 0.5
		s.position.x = roundf(base - (_focus - 320.0) * k)
		if key == "crowd":
			s.position.y = roundf(absf(sin(_t * 5.0)) * -2.0)


func _process(delta: float) -> void:
	_t += delta
	if randf() < 0.06:
		_spawn_spark()
	for s in _sparks:
		s["p"] += s["v"]
		s["v"].y += 0.12
		s["life"] -= 1
	_sparks = _sparks.filter(func(s): return s["life"] > 0)
	if _anim:
		_anim.queue_redraw()


func _spawn_spark() -> void:
	var x := randf_range(20, 620)
	match stage_id:
		"industrial_arena":
			if randf() < 0.5:
				_sparks.append({"p": Vector2(x, 60), "v": Vector2(randf_range(-0.6, 0.6), 0.5), "life": 90, "c": Color(1, 0.75, 0.3)})
		"neon_foundry":
			for i in 3:
				_sparks.append({"p": Vector2(x, 210), "v": Vector2(randf_range(-1.5, 1.5), randf_range(-2.5, -0.5)), "life": 40, "c": Color(1, 0.6, 0.2)})
		"machine_core":
			_sparks.append({"p": Vector2(x, 340), "v": Vector2(randf_range(-0.2, 0.2), -0.6), "life": 120, "c": Color(1, 0.2, 0.15, 0.7)})


## x offset of a parallax layer (positions below are in that layer's pixels)
func _lx(layer: String) -> float:
	return _layers[layer][0].position.x if _layers.has(layer) else -40.0


func _draw_anim() -> void:
	var far_x := _lx("far")
	var mid_x := _lx("mid")
	match stage_id:
		"industrial_arena":
			# hanging lamps: subtle flicker, one faulty lamp
			for i in 4:
				var x := far_x + 120.0 + i * 160.0
				var on := 0.25 + 0.1 * sin(_t * 9.0 + i * 2.0)
				if i == 2 and fmod(_t, 2.3) < 0.15:
					_anim.draw_rect(Rect2(x - 10, 40, 20, 12), Color(0, 0, 0, 0.6))
				else:
					_anim.draw_circle(Vector2(x, 47), 9, Color(1, 0.9, 0.6, on))
		"neon_foundry":
			# energy pulses travelling along the conduits
			for i in 3:
				var y := 96.0 + i * 46.0
				var px := fmod(_t * 160.0 + i * 220.0, 760.0) - 60.0
				_anim.draw_rect(Rect2(px + far_x + 40, y - 1, 24, 3), Color(0.6, 1, 1, 0.9))
				_anim.draw_rect(Rect2(px + far_x + 46, y - 2, 12, 5), Color(1, 1, 1, 0.8))
		"machine_core":
			# red warning beacons
			for i in 2:
				var x2 := mid_x + 40.0 + i * 560.0
				var on2 := fmod(_t + i * 0.5, 1.0) < 0.5
				var c := Color(1, 0.1, 0.05, 0.95 if on2 else 0.25)
				_anim.draw_rect(Rect2(x2 - 5, 70, 10, 8), c)
				if on2:
					_anim.draw_circle(Vector2(x2, 74), 16, Color(1, 0.1, 0.05, 0.18))
			# reactor core pulse
			var pulse := 0.5 + 0.5 * sin(_t * 3.0)
			var cc := Vector2(far_x + 360.0, 132)
			_anim.draw_circle(cc, 18 + pulse * 4, Color(1, 0.15, 0.1, 0.25 + 0.2 * pulse))
			_anim.draw_circle(cc, 9 + pulse * 2, Color(1, 0.6, 0.4, 0.6 + 0.3 * pulse))
	for s in _sparks:
		_anim.draw_rect(Rect2(s["p"].floor(), Vector2(2, 2)), s["c"])
