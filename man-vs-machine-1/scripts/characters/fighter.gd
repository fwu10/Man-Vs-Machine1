class_name Fighter
extends Node2D
## Shared fighter controller used by the boxer and every robot.
## The match calls tick() once per 60 Hz frame with an InputFrame from a
## player or AI controller; everything else (movement, attacks, reactions,
## animation) is driven by CharacterData so no character needs custom code.

signal attack_started(fighter: Fighter, attack: AttackData)
signal projectile_requested(fighter: Fighter, attack: AttackData)
signal effect_requested(kind: String, pos: Vector2, facing: int)
signal knocked_out(fighter: Fighter)
signal health_changed(fighter: Fighter)
signal super_started(fighter: Fighter)

enum State { INTRO, IDLE, WALK, CROUCH, JUMPSQUAT, AIR, LAND, ATTACK, BLOCKSTUN, HITSTUN,
	KD_AIR, KD_GROUND, GETUP, KO, WIN, LOSE }

const GROUND_Y := 318.0
const STAGE_LEFT := 14.0
const STAGE_RIGHT := 626.0
const FRICTION := 0.82
const JUMPSQUAT_FRAMES := 3
const LAND_FRAMES := 4
const KD_GROUND_FRAMES := 34
const GETUP_FRAMES := 22
const CANCEL_GRACE := 10        ## frames after the last active frame where cancels are still allowed
const FLASH_SHADER := preload("res://scripts/characters/fighter_flash.gdshader")

var data: CharacterData
var controller: Object
var opponent: Fighter
var player_index := 0

var health := 1000.0
var meter := 0.0
var vel := Vector2.ZERO
var facing := 1
var state: State = State.IDLE
var state_frame := 0
var airborne := false
var crouching := false
var controls_enabled := false
var guarding := false           ## showing a guard pose (holding back under threat / block button)
var threat := false             ## set by the match when the opponent is attacking nearby

var atk: AttackData
var atk_frame := 0
var atk_hits := 0
var atk_last_hit := -999
var atk_connected := false      ## hit or blocked: enables cancels
var atk_whiffed_recovery := false
var air_attack_used := false
var jump_dir := 0
var stun := 0
var hit_heavy := false
var invuln := 0
var combo_taken := 0            ## consecutive hits received in the current combo
var training_dummy := false
var last_input := InputFrame.new()

var buffer := InputBuffer.new()
var sprite: Sprite2D
var _flash := 0.0
var _flash_color := Color.WHITE
var _anim_name := ""
var _anim_time := 0.0
var _counter_ready := false
var shadow_alpha := 0.38


func setup(cdata: CharacterData, index: int) -> void:
	data = cdata
	player_index = index
	health = data.max_health
	sprite = Sprite2D.new()
	sprite.texture = data.sheet
	sprite.centered = false
	sprite.hframes = max(1, data.columns)
	sprite.vframes = max(1, data.rows)
	sprite.offset = Vector2(-data.origin.x, -data.origin.y)
	var mat := ShaderMaterial.new()
	mat.shader = FLASH_SHADER
	sprite.material = mat
	add_child(sprite)
	_play("idle")


func reset_for_round(x: float, face: int) -> void:
	position = Vector2(x, GROUND_Y)
	health = data.max_health
	vel = Vector2.ZERO
	facing = face
	airborne = false
	crouching = false
	atk = null
	stun = 0
	invuln = 0
	combo_taken = 0
	guarding = false
	buffer.clear()
	_set_state(State.IDLE)
	health_changed.emit(self)
	_update_visual(0.0)


# ------------------------------------------------------------------ queries
func is_actionable() -> bool:
	return state in [State.IDLE, State.WALK, State.CROUCH]


func is_attacking() -> bool:
	return state == State.ATTACK


func attack_phase() -> String:
	if atk == null or state != State.ATTACK:
		return ""
	if atk_frame < atk.startup:
		return "startup"
	if atk_frame < atk.startup + atk.active:
		return "active"
	return "recovery"


func is_hitbox_active() -> bool:
	return state == State.ATTACK and atk != null and atk.has_hitbox and not atk.counter \
		and attack_phase() == "active"


func is_invulnerable() -> bool:
	if invuln > 0:
		return true
	if state in [State.KD_AIR, State.KD_GROUND, State.GETUP, State.KO, State.INTRO, State.WIN, State.LOSE]:
		return true
	if state == State.ATTACK and atk != null and atk_frame <= atk.invuln_until and atk.invuln_until > 0:
		return true
	return false


func is_knocked_down() -> bool:
	return state in [State.KD_AIR, State.KD_GROUND, State.GETUP, State.KO]


func is_stunned() -> bool:
	return state in [State.HITSTUN, State.BLOCKSTUN]


func rel_x(inp: InputFrame) -> int:
	return inp.x * facing


func get_hitbox() -> Rect2:
	return _world_rect(atk.hitbox)


func get_hurtboxes() -> Array[Rect2]:
	var out: Array[Rect2] = []
	var base: Rect2
	if airborne or state == State.KD_AIR:
		base = data.hurt_air
	elif crouching or state == State.CROUCH or (state == State.ATTACK and atk != null and atk.id.begins_with("c_")):
		base = data.hurt_crouch
	else:
		base = data.hurt_stand
	out.append(_world_rect(base))
	# Extended limbs are vulnerable while attacking (lets long pokes punish whiffs).
	if state == State.ATTACK and atk != null and atk.has_hitbox and not atk.counter \
			and atk_frame >= atk.startup - 2 and atk_frame < atk.startup + atk.active + 6:
		var hb := atk.hitbox
		out.append(_world_rect(hb.grow(-hb.size.x * 0.2)))
	return out


func get_pushbox() -> Rect2:
	var h := data.hurt_stand.size.y * (0.55 if airborne else 0.85)
	return Rect2(position.x - data.push_width * 0.5, position.y - h, data.push_width, h)


func _world_rect(r: Rect2) -> Rect2:
	var x := r.position.x if facing == 1 else -(r.position.x + r.size.x)
	return Rect2(position + Vector2(x, r.position.y), r.size)


# ------------------------------------------------------------------ main tick
## Called during hit-stop: inputs are still recorded so presses are buffered.
func record_only(inp: InputFrame) -> void:
	buffer.merge_press(inp.pressed)
	last_input = inp


func tick(inp: InputFrame) -> void:
	last_input = inp
	buffer.push(inp.numpad(facing), inp.pressed)
	state_frame += 1
	if invuln > 0:
		invuln -= 1
	match state:
		State.INTRO, State.WIN, State.LOSE:
			vel.x = 0.0
		State.IDLE, State.WALK, State.CROUCH:
			_grounded(inp)
		State.JUMPSQUAT:
			if state_frame >= JUMPSQUAT_FRAMES:
				_launch_jump()
		State.AIR:
			if controls_enabled:
				_try_attack(inp, true)
		State.LAND:
			vel.x *= 0.5
			if state_frame >= LAND_FRAMES:
				_to_neutral(inp)
		State.ATTACK:
			_tick_attack(inp)
		State.HITSTUN, State.BLOCKSTUN:
			stun -= 1
			vel.x *= FRICTION
			if stun <= 0 and not airborne:
				if state == State.HITSTUN:
					combo_taken = 0
				_to_neutral(inp)
				if controls_enabled:
					_try_attack(inp, false)   # buffered reversal
		State.KD_AIR:
			pass
		State.KD_GROUND:
			vel.x *= 0.7
			if state_frame >= KD_GROUND_FRAMES:
				_set_state(State.GETUP)
				effect_requested.emit("dust", position, facing)
		State.GETUP:
			if state_frame >= GETUP_FRAMES:
				invuln = 4
				combo_taken = 0
				_set_state(State.IDLE)
		State.KO:
			vel.x *= 0.8
	_physics()


func _grounded(inp: InputFrame) -> void:
	crouching = false
	guarding = false
	if not controls_enabled:
		vel.x = 0.0
		_set_state_keep(State.IDLE)
		return
	if _try_attack(inp, false):
		return
	var rx := rel_x(inp)
	if inp.up:
		jump_dir = rx
		vel.x = 0.0
		_set_state(State.JUMPSQUAT)
		return
	if inp.down:
		crouching = true
		vel.x = 0.0
		guarding = inp.block or (rx < 0 and threat)
		_set_state_keep(State.CROUCH)
		return
	if inp.block or (rx < 0 and threat):
		guarding = true
		vel.x = 0.0
		_set_state_keep(State.IDLE)
		return
	if rx > 0:
		vel.x = data.walk_fwd * facing
		_set_state_keep(State.WALK)
	elif rx < 0:
		vel.x = -data.walk_back * facing
		_set_state_keep(State.WALK)
	else:
		vel.x = 0.0
		_set_state_keep(State.IDLE)


func _launch_jump() -> void:
	airborne = true
	air_attack_used = false
	vel = Vector2(jump_dir * data.jump_x * facing, -data.jump_velocity)
	_set_state(State.AIR)
	effect_requested.emit("jump", position, facing)


func _to_neutral(inp: InputFrame) -> void:
	if inp.down and controls_enabled:
		crouching = true
		_set_state(State.CROUCH)
	else:
		crouching = false
		_set_state(State.IDLE)


# ------------------------------------------------------------------ attacks
## Looks at buffered presses / AI requests and starts the best matching move.
## In cancel mode only moves listed in the current attack's cancel_into qualify.
func _try_attack(inp: InputFrame, in_air: bool, cancel_from: AttackData = null) -> bool:
	if inp.request != "":
		var req: String = inp.request
		if data.attacks.has(req) and _can_use(data.attacks[req], in_air, cancel_from):
			_start_attack(data.attacks[req])
			return true
		return false
	var mask_all := InputFrame.LP | InputFrame.HP | InputFrame.LK | InputFrame.HK
	var age := buffer.press_age(mask_all)
	if age < 0:
		return false
	# Specials / supers (command motions) take priority over normals.
	if not in_air:
		for sp in data.specials:
			var bmask: int = InputFrame.BUTTONS.get(sp.get("button", "hp"), InputFrame.HP)
			var pa := buffer.press_age(bmask)
			if pa < 0:
				continue
			if not buffer.motion(sp.get("motion", "FF"), pa):
				continue
			var a: AttackData = data.attacks.get(sp["attack"])
			if a and _can_use(a, false, cancel_from):
				buffer.consume(mask_all)
				_start_attack(a)
				return true
	# Normals: pick by posture and the newest pressed button.
	for b in ["hk", "hp", "lk", "lp"]:
		var m: int = InputFrame.BUTTONS[b]
		if buffer.press_age(m) < 0:
			continue
		var slot: String = b
		if in_air:
			slot = "j_" + b
		elif inp.down:
			slot = "c_" + b
		var aid: String = data.normals.get(slot, slot)
		var a2: AttackData = data.attacks.get(aid)
		if a2 and _can_use(a2, in_air, cancel_from):
			buffer.consume(mask_all)
			_start_attack(a2)
			return true
	return false


func _can_use(a: AttackData, in_air: bool, cancel_from: AttackData) -> bool:
	if a.air != in_air:
		return false
	if in_air and air_attack_used:
		return false
	if a.meter_cost > 0.0 and meter < a.meter_cost:
		return false
	if cancel_from != null:
		if a.is_super:
			return cancel_from.cancel_into.has("super") or cancel_from.cancel_into.has("special")
		if a.is_special:
			return cancel_from.cancel_into.has("special")
		return cancel_from.cancel_into.has(a.id)
	return true


func _start_attack(a: AttackData) -> void:
	atk = a
	atk_frame = 0
	atk_hits = 0
	atk_last_hit = -999
	atk_connected = false
	_counter_ready = a.counter
	if a.meter_cost > 0.0:
		meter -= a.meter_cost
	if a.air:
		air_attack_used = true
	else:
		vel.x = 0.0
	crouching = a.id.begins_with("c_")
	_set_state(State.ATTACK)
	attack_started.emit(self, a)
	if a.is_super:
		super_started.emit(self)
	if a.strength == "heavy" or a.is_special:
		Audio.play_sfx("whoosh_h")
	else:
		Audio.play_sfx("whoosh_l")


func _tick_attack(inp: InputFrame) -> void:
	atk_frame += 1
	var a := atk
	# Scripted movement
	if not airborne:
		var moving := false
		for m in a.move:
			if atk_frame >= int(m[0]) and atk_frame <= int(m[1]):
				vel.x = float(m[2]) * facing
				moving = true
		if not moving and not a.air:
			vel.x *= 0.6
	if a.air_launch != Vector3.ZERO and atk_frame == int(a.air_launch.x):
		airborne = true
		air_attack_used = true
		vel = Vector2(a.air_launch.y * facing, a.air_launch.z)
	if atk_frame == a.startup:
		if not a.projectile.is_empty():
			projectile_requested.emit(self, a)
		if a.teleport and opponent:
			_teleport_behind()
	if a.fx != "" and atk_frame == 1:
		effect_requested.emit(a.fx, position, facing)
	# Cancels: after the move connects, a listed follow-up may interrupt it.
	if atk_connected and a.cancel_into.size() > 0 and controls_enabled:
		if atk_frame <= a.startup + a.active + CANCEL_GRACE:
			if _try_attack(inp, airborne, a):
				return
	if atk_frame >= a.total_frames():
		if a.counter and _counter_ready:
			pass
		if airborne:
			_set_state(State.AIR)
		else:
			atk = null
			_to_neutral(inp)


func _teleport_behind() -> void:
	var side := signf(opponent.position.x - position.x)
	if side == 0:
		side = 1
	var target := opponent.position.x + side * 70.0
	if target < STAGE_LEFT + 30 or target > STAGE_RIGHT - 30:
		target = opponent.position.x - side * 130.0
	effect_requested.emit("phase", position, facing)
	position.x = clampf(target, STAGE_LEFT + 30, STAGE_RIGHT - 30)
	facing = 1 if opponent.position.x > position.x else -1
	effect_requested.emit("phase", position, facing)


## Called by the match when this fighter's hit/block connected.
func on_attack_connected(result: String) -> void:
	if atk == null:
		return   # traded: this fighter was hit on the same frame
	atk_hits += 1
	atk_last_hit = atk_frame
	atk_connected = true
	if result == "hit":
		meter = min(100.0, meter + 4.0 + atk.damage * 0.08)
	elif result == "block":
		meter = min(100.0, meter + 2.0)


func can_hit_now() -> bool:
	if atk == null:
		return false
	return atk_hits < atk.hits and (atk_hits == 0 or atk_frame - atk_last_hit >= atk.hit_interval)


func in_counter_window() -> bool:
	return state == State.ATTACK and atk != null and atk.counter and _counter_ready \
		and atk_frame >= atk.startup and atk_frame < atk.startup + atk.active


func trigger_counter() -> void:
	_counter_ready = false
	var ca: AttackData = data.attacks.get(atk.counter_attack)
	effect_requested.emit("parry", position + Vector2(18 * facing, -60), facing)
	Audio.play_sfx("parry")
	if ca:
		_start_attack(ca)
		invuln = ca.startup + 2


# ------------------------------------------------------------------ being hit
func can_block(a: AttackData, from_x: float) -> bool:
	if not a.blockable or not controls_enabled or airborne:
		return false
	if not (state in [State.IDLE, State.WALK, State.CROUCH, State.BLOCKSTUN]):
		return false
	var away := -signf(from_x - position.x)
	var holding_back := last_input.x != 0 and signf(last_input.x) == away
	if not (holding_back or last_input.block):
		return false
	var crouch_block := last_input.down
	if crouch_block and a.level == "overhead":
		return false
	if not crouch_block and a.level == "low":
		return false
	return true


## Applies an attack to this fighter. Returns "hit", "block", "armor" or "parry".
func receive_hit(attacker: Fighter, a: AttackData, from_x: float, scale_damage := true) -> String:
	var dir := signf(position.x - from_x)
	if dir == 0:
		dir = -facing
	if in_counter_window() and a.projectile.is_empty():
		trigger_counter()
		return "parry"
	if can_block(a, from_x):
		_set_state(State.BLOCKSTUN)
		stun = a.blockstun
		crouching = last_input.down
		vel.x = a.block_push * dir / data.weight
		_damage(a.chip)
		meter = min(100.0, meter + 3.0)
		_flash_now(Color(0.5, 0.8, 1.0), 0.45)
		return "block"
	if state == State.ATTACK and atk != null and atk_frame <= atk.armor_until and atk.armor_until > 0:
		_damage(a.damage * 0.5)
		_flash_now(Color(1.0, 0.45, 0.3), 1.0)
		if health <= 0:
			_knockout(dir, a)
		return "armor"
	var scale := 1.0
	if scale_damage:
		scale = maxf(0.35, 1.0 - 0.1 * combo_taken)
	combo_taken += 1
	_damage(a.damage * scale)
	meter = min(100.0, meter + 2.0 + a.damage * 0.05)
	_flash_now(Color.WHITE, 0.55 if a.strength == "heavy" else 0.4)
	atk = null
	if health <= 0:
		_knockout(dir, a)
		return "hit"
	if a.knockdown or airborne or state in [State.AIR, State.JUMPSQUAT]:
		_set_state(State.KD_AIR)
		airborne = true
		vel = Vector2(a.launch.x * dir / data.weight, a.launch.y)
		if not a.knockdown:
			vel = Vector2(2.2 * dir, -4.2)
		return "hit"
	hit_heavy = a.strength == "heavy"
	_set_state(State.HITSTUN)
	stun = a.hitstun
	vel.x = a.knockback * dir / data.weight
	return "hit"


func _damage(amount: float) -> void:
	if training_dummy:
		health = max(1.0, health - amount)
	else:
		health = max(0.0, health - amount)
	health_changed.emit(self)


func _knockout(dir: float, _a: AttackData) -> void:
	airborne = true
	vel = Vector2(3.4 * dir, -6.0)
	controls_enabled = false
	_set_state(State.KO)
	knocked_out.emit(self)


func _flash_now(c: Color, amount: float) -> void:
	_flash_color = c
	_flash = amount


func set_result_pose(won: bool) -> void:
	if state == State.KO:
		return
	controls_enabled = false
	atk = null
	vel.x = 0
	if airborne:
		return
	_set_state(State.WIN if won else State.LOSE)


func play_intro() -> void:
	_set_state(State.INTRO)


# ------------------------------------------------------------------ physics
func _physics() -> void:
	if airborne:
		vel.y += data.gravity
	position += vel
	if airborne and position.y >= GROUND_Y and vel.y >= 0.0:
		position.y = GROUND_Y
		airborne = false
		vel.y = 0.0
		_on_landed()
	position.x = clampf(position.x, STAGE_LEFT + data.push_width * 0.5, STAGE_RIGHT - data.push_width * 0.5)


func _on_landed() -> void:
	match state:
		State.AIR:
			_set_state(State.LAND)
			effect_requested.emit("land", position, facing)
			Audio.play_sfx("land")
		State.ATTACK:
			atk = null
			_set_state(State.LAND)
			effect_requested.emit("land", position, facing)
		State.KD_AIR:
			_set_state(State.KD_GROUND)
			effect_requested.emit("dust", position, facing)
			Audio.play_sfx("thud")
		State.KO:
			effect_requested.emit("dust", position, facing)
			Audio.play_sfx("thud")
			vel.x *= 0.4
		State.HITSTUN, State.BLOCKSTUN:
			pass


func at_wall() -> bool:
	return position.x <= STAGE_LEFT + data.push_width * 0.5 + 1 or position.x >= STAGE_RIGHT - data.push_width * 0.5 - 1


func update_facing() -> void:
	if opponent == null or airborne:
		return
	if state in [State.IDLE, State.WALK, State.CROUCH, State.LAND, State.JUMPSQUAT]:
		var dx := opponent.position.x - position.x
		if absf(dx) > 2.0:
			facing = 1 if dx > 0 else -1


# ------------------------------------------------------------------ state + visuals
func _set_state(s: State) -> void:
	state = s
	state_frame = 0
	if s != State.ATTACK:
		atk = null


func _set_state_keep(s: State) -> void:
	if state != s:
		_set_state(s)


func _play(anim_name: String) -> void:
	if _anim_name != anim_name:
		_anim_name = anim_name
		_anim_time = 0.0


func _set_frame(anim_name: String, idx: int) -> void:
	var a: Dictionary = data.anims.get(anim_name, data.anims.get("idle"))
	var n := int(a.get("frames", 1))
	idx = clampi(idx, 0, n - 1)
	sprite.frame = int(a.get("row", 0)) * data.columns + idx


func _loop_frame(anim_name: String, delta: float) -> void:
	_play(anim_name)
	_anim_time += delta
	var a: Dictionary = data.anims.get(anim_name, {})
	var n := int(a.get("frames", 1))
	var fps := float(a.get("fps", 8))
	var i := int(_anim_time * fps)
	if a.get("loop", false):
		i = i % n
	_set_frame(anim_name, i)


func _update_visual(delta: float) -> void:
	sprite.flip_h = facing < 0
	var sf := state_frame
	match state:
		State.INTRO:
			_loop_frame("intro", delta)
		State.IDLE:
			if guarding:
				_loop_frame("block", delta)
			else:
				_loop_frame("idle", delta)
		State.WALK:
			if vel.x * facing >= 0:
				_loop_frame("walk_fwd", delta)
			else:
				_loop_frame("walk_back", delta)
		State.CROUCH:
			_loop_frame("block_crouch" if guarding else "crouch", delta)
		State.JUMPSQUAT, State.LAND:
			_loop_frame("land", delta)
		State.AIR:
			_play("jump")
			_set_frame("jump", 0 if vel.y < -2.5 else (1 if vel.y < 2.5 else 2))
		State.ATTACK:
			_play(atk.anim)
			_set_frame(atk.anim, _attack_anim_frame())
		State.BLOCKSTUN:
			_loop_frame("block_crouch" if crouching else "block", delta)
		State.HITSTUN:
			var an := "hit_crouch" if crouching else ("hit_heavy" if hit_heavy else "hit_light")
			_play(an)
			_set_frame(an, 0 if sf < max(3, stun / 2) else 1)
		State.KD_AIR:
			_play("knockdown")
			_set_frame("knockdown", 0 if vel.y < 0 else 1)
		State.KD_GROUND:
			_play("knockdown")
			_set_frame("knockdown", 2 if sf < 6 else 3)
		State.KO:
			_play("knockdown")
			if airborne:
				_set_frame("knockdown", 0 if vel.y < 0 else 1)
			else:
				_set_frame("knockdown", 2 if sf < 6 else 3)
		State.GETUP:
			_play("getup")
			_set_frame("getup", int(sf * 3 / GETUP_FRAMES))
		State.WIN:
			_loop_frame("victory", delta)
		State.LOSE:
			_loop_frame("defeat", delta)
	var mat := sprite.material as ShaderMaterial
	mat.set_shader_parameter("flash", _flash)
	mat.set_shader_parameter("flash_color", _flash_color)
	# invulnerable getup / teleport flicker
	if state == State.ATTACK and atk != null and atk.teleport and atk_frame < atk.startup + 6:
		sprite.visible = (atk_frame / 2) % 2 == 0
	else:
		sprite.visible = true
	queue_redraw()


## Maps the attack's startup/active/recovery phases onto the animation frames
## so the drawn strike always lines up with the live hitbox.
func _attack_anim_frame() -> int:
	var a: Dictionary = data.anims.get(atk.anim, {})
	var n := int(a.get("frames", 1))
	var act: PackedInt32Array = atk.anim_active
	if act.is_empty():
		# no strike frames: spread the whole move evenly
		return int(float(atk_frame) / maxi(1, atk.total_frames()) * n)
	var a0 := act[0]
	var a1 := act[act.size() - 1]
	if atk_frame < atk.startup:
		return int(float(atk_frame) / atk.startup * a0) if a0 > 0 else 0
	if atk_frame < atk.startup + atk.active:
		var t := float(atk_frame - atk.startup) / atk.active
		return a0 + int(t * (a1 - a0 + 1))
	var rec_frames := n - 1 - a1
	if rec_frames <= 0:
		return a1
	var t2 := float(atk_frame - atk.startup - atk.active) / maxi(1, atk.recovery)
	return min(n - 1, a1 + 1 + int(t2 * rec_frames))


func _draw() -> void:
	# ground shadow (stays on the floor while jumping)
	var gy := GROUND_Y - position.y
	var h := clampf(1.0 - (-gy) / 140.0, 0.35, 1.0)
	var w := data.push_width * 0.95 * h
	var pts := PackedVector2Array()
	for i in 16:
		var ang := TAU * i / 16.0
		pts.append(Vector2(cos(ang) * w, gy + sin(ang) * 3.5 * h))
	draw_colored_polygon(pts, Color(0, 0, 0, shadow_alpha * h))


func visual_tick(delta: float) -> void:
	if _flash > 0.0:
		_flash = maxf(0.0, _flash - 0.09)
	_update_visual(delta)
