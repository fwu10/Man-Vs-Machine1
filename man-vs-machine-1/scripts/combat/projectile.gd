class_name Projectile
extends Node2D
## Fireball-style attacks. Uses the owner's AttackData for damage/stun rules.
## Kinds:
##   bolt / pellet : travel horizontally
##   wave          : travels along the floor (a low; jump or crouch-block it)
##   orbital       : warning marker at a fixed x, then a strike from above

var owner_fighter: Fighter
var attack: AttackData
var kind := "bolt"
var vel := Vector2.ZERO
var size := Vector2(18, 12)
var life := 120
var delay := 0              ## warning frames before becoming dangerous
var active_frames := 10     ## orbital: how long the strike column lasts
var hits_left := 1
var color := Color(0.4, 0.9, 1.0)
var age := 0
var dead := false


func configure(f: Fighter, a: AttackData, spec: Dictionary, x_override := INF) -> void:
	owner_fighter = f
	attack = a
	kind = spec.get("kind", "bolt")
	var face := f.facing
	size = Vector2(spec.get("w", 18), spec.get("h", 12))
	life = int(spec.get("life", 150))
	color = Color(spec.get("color", "#66e6ff"))
	hits_left = int(spec.get("hits", 1))
	delay = int(spec.get("delay", 0))
	active_frames = int(spec.get("active", 10))
	if kind == "orbital":
		var x: float = x_override if x_override != INF else f.opponent.position.x
		position = Vector2(x, Fighter.GROUND_Y)
		vel = Vector2.ZERO
		life = delay + active_frames + 12
	else:
		position = f.position + Vector2(float(spec.get("x", 30)) * face, float(spec.get("y", -60)))
		vel = Vector2(float(spec.get("speed", 4.0)) * face, 0)


func is_dangerous() -> bool:
	if dead:
		return false
	if kind == "orbital":
		return age >= delay and age < delay + active_frames
	return age >= delay


func get_hitbox() -> Rect2:
	if kind == "orbital":
		return Rect2(position.x - size.x * 0.5, position.y - 360, size.x, 360)
	return Rect2(position - size * 0.5, size)


func tick() -> void:
	age += 1
	if age >= delay:
		position += vel
	if age == delay and kind == "orbital":
		Audio.play_sfx("laser")
	life -= 1
	if life <= 0 or position.x < -40 or position.x > 680:
		dead = true
	queue_redraw()


func on_hit() -> void:
	hits_left -= 1
	if hits_left <= 0 and kind != "orbital":
		dead = true


func _draw() -> void:
	var t := age
	match kind:
		"orbital":
			var warn := age < delay
			if warn:
				# blinking target reticle on the floor
				var on := (t / 4) % 2 == 0
				var c := Color(1, 0.15, 0.1, 0.9 if on else 0.4)
				var w := size.x * 0.5 + 6 - (t % 8)
				draw_rect(Rect2(-w, -3, w * 2, 3), c)
				draw_line(Vector2(0, -12), Vector2(0, 0), c, 2)
				draw_rect(Rect2(-size.x * 0.5, -400, size.x, 400), Color(1, 0.1, 0.1, 0.07 + 0.05 * float(on)))
			elif age < delay + active_frames:
				var k := 1.0 - float(age - delay) / active_frames
				draw_rect(Rect2(-size.x * 0.5 - 4, -400, size.x + 8, 400), Color(1, 0.3, 0.2, 0.35 * k))
				draw_rect(Rect2(-size.x * 0.5, -400, size.x, 400), Color(1, 0.55, 0.4, 0.9 * k))
				draw_rect(Rect2(-size.x * 0.2, -400, size.x * 0.4, 400), Color(1, 1, 0.9, k))
				draw_rect(Rect2(-size.x, -6, size.x * 2, 6), Color(1, 0.8, 0.5, k))
		"wave":
			var h := size.y
			for i in 5:
				var x := -size.x * 0.5 + i * size.x / 5.0
				var hh := h * (0.5 + 0.5 * absf(sin((t + i * 3) * 0.5)))
				draw_rect(Rect2(x, size.y * 0.5 - hh, size.x / 5.0 - 1, hh), color)
			draw_rect(Rect2(-size.x * 0.5, size.y * 0.5 - 2, size.x, 2), Color(1, 1, 1, 0.8))
		_:
			var dirx := signf(vel.x) if vel.x != 0 else 1.0
			# trail
			for i in range(1, 5):
				var a := 0.5 - i * 0.1
				draw_rect(Rect2(Vector2(-dirx * i * 7 - size.x * 0.35, -size.y * 0.35), size * 0.7), Color(color, a))
			draw_rect(Rect2(-size * 0.5, size), color)
			draw_rect(Rect2(-size * 0.3, size * 0.6), Color(1, 1, 1, 0.95))
			if kind == "bolt":
				# crackling arcs
				for i in 3:
					var y := (randi() % int(size.y)) - size.y * 0.5
					draw_line(Vector2(-size.x * 0.5, y), Vector2(size.x * 0.5 + 4 * dirx, -y), Color(0.8, 1, 1, 0.9), 1)
