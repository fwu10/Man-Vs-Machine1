class_name EffectsLayer
extends Node2D
## Lightweight pixel-art effects drawn procedurally: hit sparks, block
## flashes, metal sparks, dust, parry rings, teleport glitches and the
## boss beam. Effects are plain dictionaries updated every frame.

var _fx: Array[Dictionary] = []
var _particles: Array[Dictionary] = []


func spawn(kind: String, pos: Vector2, facing := 1, extra := {}) -> void:
	var life := 12
	match kind:
		"hit_l": life = 9
		"hit_h": life = 14
		"block": life = 10
		"dust", "land", "jump": life = 18
		"parry": life = 16
		"phase": life = 14
		"beam", "charge": life = int(extra.get("life", 60))
		"electric": life = 30
		"ko": life = 30
	var e := {"kind": kind, "pos": pos, "age": 0, "life": life, "facing": facing}
	e.merge(extra)
	_fx.append(e)
	match kind:
		"hit_h", "spark_burst":
			_burst(pos, 10, Color(1, 0.85, 0.4), 3.5, facing)
		"hit_l":
			_burst(pos, 5, Color(1, 0.95, 0.7), 2.5, facing)
		"metal":
			_burst(pos, 9, Color(1, 0.7, 0.25), 4.0, facing)
		"dust", "land":
			for i in 8:
				_particles.append({"p": pos + Vector2(randf_range(-14, 14), -2), "v": Vector2(randf_range(-1.2, 1.2), randf_range(-1.2, -0.2)),
					"life": randi_range(14, 24), "c": Color(0.75, 0.7, 0.62, 0.8), "g": 0.0, "s": 3})
		"ko":
			_burst(pos, 26, Color(1, 0.9, 0.5), 5.0, facing)
		"explosion":
			_burst(pos, 18, Color(1, 0.55, 0.2), 4.5, facing)
			_fx[-1]["life"] = 20


func _burst(pos: Vector2, n: int, c: Color, spd: float, facing: int) -> void:
	for i in n:
		var ang := randf_range(-PI, PI)
		var v := Vector2(cos(ang), sin(ang)) * randf_range(spd * 0.4, spd)
		v.x += facing * 0.8
		_particles.append({"p": pos, "v": v, "life": randi_range(10, 22), "c": c, "g": 0.18, "s": 2})


func clear() -> void:
	_fx.clear()
	_particles.clear()


func _physics_process(_delta: float) -> void:
	for e in _fx:
		e["age"] += 1
	_fx = _fx.filter(func(e): return e["age"] < e["life"])
	for p in _particles:
		p["p"] += p["v"]
		p["v"].y += p["g"]
		p["v"] *= 0.96
		p["life"] -= 1
	_particles = _particles.filter(func(p): return p["life"] > 0)
	queue_redraw()


func _draw() -> void:
	for p in _particles:
		var s: int = p["s"]
		draw_rect(Rect2(p["p"].floor(), Vector2(s, s)), p["c"])
	for e in _fx:
		var k: float = float(e["age"]) / e["life"]
		var pos: Vector2 = e["pos"]
		match e["kind"]:
			"hit_l", "hit_h":
				var big: bool = e["kind"] == "hit_h"
				var r := (10.0 if big else 6.0) + k * (14.0 if big else 8.0)
				var col := Color(1, 1, 0.85, 1.0 - k)
				_star(pos, r, 8 if big else 6, col, 3 if big else 2)
				if e["age"] < 3:
					draw_circle(pos, r * 0.6, Color(1, 1, 1, 0.95))
			"metal":
				_star(pos, 6 + k * 10, 6, Color(1, 0.8, 0.4, 1.0 - k), 2)
			"block":
				var r2 := 8.0 + k * 10.0
				var c2 := Color(0.55, 0.85, 1.0, 1.0 - k)
				var f: int = e["facing"]
				for i in 7:
					var a := (-0.9 + i * 0.3)
					var d := Vector2(cos(a) * -f, sin(a))
					draw_rect(Rect2((pos + d * r2).floor(), Vector2(3, 3)), c2)
				draw_line(pos + Vector2(-f * 4, -r2), pos + Vector2(-f * 4, r2), c2, 2)
			"parry":
				var r3 := 6.0 + k * 26.0
				_ring(pos, r3, Color(1, 0.25, 0.25, 1.0 - k))
				_ring(pos, r3 * 0.6, Color(1, 1, 1, 1.0 - k))
			"phase":
				for i in 6:
					var y := -10 - i * 16 + randi_range(-3, 3)
					var w := randi_range(14, 40) * (1.0 - k)
					draw_rect(Rect2(pos.x - w * 0.5 + randi_range(-6, 6), pos.y + y, w, 3), Color(1, 0.2, 0.3, 0.8 * (1.0 - k)))
			"jump":
				draw_rect(Rect2(pos.x - 12 - k * 8, pos.y - 2, 6, 2), Color(1, 1, 1, 0.6 * (1.0 - k)))
				draw_rect(Rect2(pos.x + 6 + k * 8, pos.y - 2, 6, 2), Color(1, 1, 1, 0.6 * (1.0 - k)))
			"electric":
				var o: Fighter = e.get("owner")
				if o and is_instance_valid(o):
					for i in 3:
						var a0 := o.position + Vector2(randf_range(-16, 16), randf_range(-90, -10))
						var a1 := a0 + Vector2(randf_range(-12, 12), randf_range(-12, 12))
						draw_line(a0, a1, Color(0.6, 1, 1, 0.9), 1)
			"charge":
				var o2: Fighter = e.get("owner")
				if o2 and is_instance_valid(o2):
					var c := o2.position + Vector2(30 * o2.facing, -80)
					var rr := 18.0 * (1.0 - k) + 3
					_ring(c, rr, Color(1, 0.2, 0.2, 0.9))
					draw_circle(c, 3 + k * 4, Color(1, 0.6, 0.5, 0.9))
			"beam":
				_draw_beam(e)
			"ko":
				_ring(pos, 10 + k * 60, Color(1, 1, 1, 1.0 - k))
			"explosion":
				var r4 := 6 + k * 22
				draw_circle(pos, r4, Color(1, 0.5, 0.15, 1.0 - k))
				draw_circle(pos, r4 * 0.6, Color(1, 0.9, 0.5, 1.0 - k))


## Overlord's beam: blinking warning line during startup, then a thick beam.
func _draw_beam(e: Dictionary) -> void:
	var o: Fighter = e.get("owner")
	if o == null or not is_instance_valid(o) or o.atk == null or o.atk.fx != "beam":
		e["age"] = e["life"]
		return
	var a := o.atk
	var y := o.position.y + a.hitbox.position.y + a.hitbox.size.y * 0.5
	var x0 := o.position.x + 40 * o.facing
	var x1 := 700.0 if o.facing > 0 else -60.0
	if o.atk_frame < a.startup:
		var on := (o.atk_frame / 3) % 2 == 0
		draw_line(Vector2(x0, y), Vector2(x1, y), Color(1, 0.1, 0.1, 0.9 if on else 0.35), 1)
		var r := 4.0 + 10.0 * float(o.atk_frame) / a.startup
		draw_circle(Vector2(x0, y), r, Color(1, 0.3, 0.2, 0.8))
		draw_circle(Vector2(x0, y), r * 0.5, Color(1, 0.9, 0.8, 0.9))
	elif o.atk_frame < a.startup + a.active:
		var h := a.hitbox.size.y
		var wob := sin(o.atk_frame * 1.3) * 2
		draw_rect(Rect2(min(x0, x1), y - h * 0.5 - 3 - wob, absf(x1 - x0), h + 6 + wob * 2), Color(1, 0.15, 0.1, 0.5))
		draw_rect(Rect2(min(x0, x1), y - h * 0.5, absf(x1 - x0), h), Color(1, 0.5, 0.35, 0.95))
		draw_rect(Rect2(min(x0, x1), y - h * 0.2, absf(x1 - x0), h * 0.4), Color(1, 1, 0.92, 1))
		draw_circle(Vector2(x0, y), h * 0.9, Color(1, 0.85, 0.7))
	elif o.atk_frame > a.startup + a.active + 8:
		e["age"] = e["life"]


func _star(c: Vector2, r: float, spikes: int, col: Color, w: int) -> void:
	for i in spikes:
		var a := TAU * i / spikes + 0.3
		var d := Vector2(cos(a), sin(a))
		draw_line(c + d * r * 0.3, c + d * r, col, w)


func _ring(c: Vector2, r: float, col: Color) -> void:
	var n := 20
	for i in n:
		var a := TAU * i / n
		draw_rect(Rect2((c + Vector2(cos(a), sin(a)) * r).floor(), Vector2(2, 2)), col)
