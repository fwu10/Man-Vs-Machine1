class_name AIController
extends RefCounted
## Robot opponent brain. Produces the same InputFrames a human would, so the
## AI plays by the same combat rules. It perceives the opponent through a
## reaction delay and acts according to a per-robot profile (data/characters).

enum AIState { IDLE, APPROACH, RETREAT, ATTACK, DEFEND, JUMP, RECOVER, STUNNED, KNOCKED_DOWN, DEFEATED }
const STATE_NAMES := ["IDLE", "APPROACH", "RETREAT", "ATTACK", "DEFEND", "JUMP", "RECOVER", "STUNNED", "KNOCKED DOWN", "DEFEATED"]

var p: Dictionary            ## effective profile after difficulty scaling
var ai_state: AIState = AIState.IDLE
var _timer := 0
var _think := 0
var _history: Array[Dictionary] = []
var _queued := ""
var _defend_low := false
var _combo_from := ""
var _jump_attack_done := false
var _rng := RandomNumberGenerator.new()
var _match_projectiles: Callable   ## returns Array of opponent projectiles


func _init(profile: Dictionary, difficulty := 0.5) -> void:
	_rng.randomize()
	p = profile.duplicate(true)
	var d := clampf(difficulty, 0.0, 1.2)
	p["reaction"] = int(round(float(p.get("reaction", 16)) * (1.35 - 0.55 * d)))
	for key in ["block", "anti_air", "punish", "combo", "parry"]:
		p[key] = clampf(float(p.get(key, 0.3)) * (0.7 + 0.5 * d), 0.0, 0.92)
	p["aggression"] = clampf(float(p.get("aggression", 0.5)) * (0.8 + 0.35 * d), 0.05, 0.95)


func set_projectile_source(c: Callable) -> void:
	_match_projectiles = c


func state_name() -> String:
	return STATE_NAMES[ai_state]


func _snapshot(o: Fighter) -> Dictionary:
	return {
		"x": o.position.x, "y": o.position.y, "air": o.airborne, "vx": o.vel.x, "vy": o.vel.y,
		"phase": o.attack_phase(), "atk": o.atk.id if o.atk else "",
		"level": o.atk.level if o.atk else "", "crouch": o.crouching,
		"reach": (o.atk.hitbox.position.x + o.atk.hitbox.size.x) if (o.atk and o.atk.has_hitbox) else 0.0,
		"down": o.is_knocked_down(), "stun": o.is_stunned(),
	}


func get_input(f: Fighter) -> InputFrame:
	var i := InputFrame.new()
	var o := f.opponent
	_history.append(_snapshot(o))
	if _history.size() > 40:
		_history.pop_front()
	var seen: Dictionary = _history[max(0, _history.size() - 1 - int(p["reaction"]))]
	var toward := 1 if o.position.x > f.position.x else -1
	var dist := absf(o.position.x - f.position.x)

	# ---- states the AI cannot act in
	if f.state == Fighter.State.KO:
		ai_state = AIState.DEFEATED
		return i
	if f.is_knocked_down():
		ai_state = AIState.KNOCKED_DOWN
		_timer = 0
		return i
	if f.state == Fighter.State.HITSTUN:
		ai_state = AIState.STUNNED
		return i
	if f.state == Fighter.State.BLOCKSTUN:
		# keep guarding while in blockstun
		ai_state = AIState.DEFEND
		i.x = -toward
		i.down = _defend_low
		return i
	if not f.controls_enabled:
		ai_state = AIState.IDLE
		return i

	# ---- mid-attack: optional combo follow-up
	if f.is_attacking():
		ai_state = AIState.RECOVER if f.attack_phase() == "recovery" else AIState.ATTACK
		if f.atk_connected and f.atk.id != _combo_from:
			_combo_from = f.atk.id
			var combos: Dictionary = p.get("combos", {})
			if combos.has(f.atk.id) and _rng.randf() < float(p["combo"]):
				var opts: Array = combos[f.atk.id]
				var nxt: String = opts[_rng.randi() % opts.size()]
				if _usable(f, nxt):
					i.request = nxt
		return i
	_combo_from = ""

	# ---- airborne: jump-in attack timing
	if f.airborne:
		ai_state = AIState.JUMP
		if not _jump_attack_done and f.vel.y > -1.0 and dist < 80:
			_jump_attack_done = true
			i.request = p.get("jump_attack", "j_k")
		return i
	_jump_attack_done = false

	# ---- reactions (use delayed perception)
	_timer -= 1
	_think -= 1
	var urgent := _react(f, seen, dist)
	if urgent != "":
		_queued = urgent
		_timer = 0
	elif _timer <= 0 and _think <= 0:
		_decide(f, seen, dist)
		_think = max(3, int(p["reaction"]) / 3)

	# ---- execute the current intent
	match ai_state:
		AIState.APPROACH:
			i.x = toward
		AIState.RETREAT:
			i.x = -toward
		AIState.DEFEND:
			i.x = -toward
			i.down = _defend_low
		AIState.JUMP:
			i.up = true
			i.x = toward if _rng.randf() < 0.85 else 0
			ai_state = AIState.IDLE
		AIState.IDLE:
			pass
	if _queued != "":
		if _usable(f, _queued):
			i.request = _queued
			ai_state = AIState.ATTACK
			if _queued.begins_with("c_"):
				i.down = true
		_queued = ""
	return i


## Immediate responses to what the AI has "seen" (already delayed).
func _react(f: Fighter, seen: Dictionary, dist: float) -> String:
	var phase: String = seen["phase"]
	# anti-air
	if seen["air"] and dist < 120 and seen["vy"] > -3.0:
		if _rng.randf() < float(p["anti_air"]) * 0.25:
			var aa: Array = p.get("anti_air_moves", ["c_hp"])
			return aa[_rng.randi() % aa.size()]
		if ai_state != AIState.DEFEND and _rng.randf() < float(p["block"]) * 0.3:
			_start(AIState.DEFEND, 24)
			_defend_low = false
		return ""
	# incoming strike
	if phase in ["startup", "active"] and dist < float(seen["reach"]) + 40.0:
		if ai_state == AIState.DEFEND:
			return ""
		if p.has("parry_move") and _rng.randf() < float(p["parry"]) * 0.35:
			return p["parry_move"]
		if p.has("armor_move") and _rng.randf() < float(p.get("armor", 0.0)) * 0.3:
			return p["armor_move"]
		if _rng.randf() < float(p["block"]) * 0.45:
			_defend_low = seen["level"] == "low" or seen["crouch"]
			_start(AIState.DEFEND, 16 + _rng.randi() % 10)
		return ""
	# projectiles
	if _match_projectiles.is_valid():
		for pr in _match_projectiles.call(f):
			var pd := absf(pr.position.x - f.position.x)
			if pd < 140 and ai_state != AIState.DEFEND and ai_state != AIState.JUMP:
				var r := _rng.randf()
				if pr.kind == "orbital":
					if r < float(p["block"]) * 0.2:
						_start(AIState.RETREAT if absf(pr.position.x - f.position.x) < 30 else AIState.IDLE, 20)
				elif r < float(p.get("jump", 0.1)) * 0.25:
					_start(AIState.JUMP, 1)
				elif r < float(p["block"]) * 0.2:
					_defend_low = pr.kind == "wave"
					_start(AIState.DEFEND, 30)
				return ""
	# punish whiffs
	if phase == "recovery" and _rng.randf() < float(p["punish"]) * 0.3:
		var mv := _pick(f, p.get("punish_moves", ["hp"]), dist)
		if mv != "":
			return mv
	return ""


## Neutral-game decision made every few frames.
func _decide(f: Fighter, seen: Dictionary, dist: float) -> void:
	var rng := float(p.get("range", 70))
	var aggr := float(p["aggression"])
	var special := float(p.get("special", 0.15))
	if f.health < f.data.max_health * 0.5 and p.get("phase2", false):
		aggr = min(0.95, aggr + 0.2)
		special = min(0.8, special + 0.15)
	if seen["down"]:
		# opponent on the floor: close in to pressure the wake-up
		_start(AIState.APPROACH if dist > rng else AIState.IDLE, 10)
		return
	# pre-emptive guard: inside the opponent's striking range, sometimes just defend
	if dist < 95.0 and not seen["air"] and _rng.randf() < float(p["block"]) * 0.22:
		_defend_low = _rng.randf() < 0.45
		_start(AIState.DEFEND, 10 + _rng.randi() % 14)
		return
	var r := _rng.randf()
	if dist > rng + 30:
		var proj: Array = p.get("far_specials", [])
		if proj.size() > 0 and r < special:
			_queued = proj[_rng.randi() % proj.size()]
			_start(AIState.IDLE, 20 + _rng.randi() % 20)
		elif r < special + float(p.get("jump", 0.1)) and dist < 200:
			_start(AIState.JUMP, 1)
		else:
			_start(AIState.APPROACH, 10 + _rng.randi() % 20)
		return
	if dist < rng - 30 and _rng.randf() < float(p.get("retreat", 0.2)):
		_start(AIState.RETREAT, 10 + _rng.randi() % 14)
		return
	if r < aggr:
		var bucket := "close" if dist < 60 else "mid"
		var table: Array = p.get(bucket, [["lp", 1]])
		var mv := _weighted(f, table, dist)
		if mv != "":
			_queued = mv
			_start(AIState.IDLE, 6 + _rng.randi() % int(p.get("pause", 14)))
			return
		_start(AIState.APPROACH, 6)
		return
	# spacing dance
	var choice := _rng.randf()
	if choice < 0.4:
		_start(AIState.APPROACH, 6 + _rng.randi() % 10)
	elif choice < 0.65:
		_start(AIState.RETREAT, 6 + _rng.randi() % 8)
	elif choice < 0.65 + float(p.get("jump", 0.1)):
		_start(AIState.JUMP, 1)
	else:
		_start(AIState.IDLE, 8 + _rng.randi() % 14)


func _start(s: AIState, frames: int) -> void:
	ai_state = s
	_timer = frames


func _usable(f: Fighter, aid: String) -> bool:
	var a: AttackData = f.data.attacks.get(aid)
	return a != null and (a.meter_cost <= 0.0 or f.meter >= a.meter_cost)


func _reach(f: Fighter, aid: String) -> float:
	var a: AttackData = f.data.attacks.get(aid)
	if a == null:
		return 0.0
	if not a.projectile.is_empty():
		return 640.0
	if not a.has_hitbox:
		return 0.0
	var travel := 0.0
	for m in a.move:
		travel += (float(m[1]) - float(m[0]) + 1.0) * float(m[2])
	return a.hitbox.position.x + a.hitbox.size.x + travel


func _pick(f: Fighter, moves: Array, dist: float) -> String:
	var ok: Array = []
	for m in moves:
		if _usable(f, m) and _reach(f, m) + 10.0 >= dist:
			ok.append(m)
	if ok.is_empty():
		return ""
	return ok[_rng.randi() % ok.size()]


func _weighted(f: Fighter, table: Array, dist: float) -> String:
	var total := 0.0
	var ok: Array = []
	for e in table:
		var mv: String = e[0]
		if _usable(f, mv) and _reach(f, mv) + 6.0 >= dist:
			ok.append(e)
			total += float(e[1])
	if ok.is_empty():
		return ""
	var r := _rng.randf() * total
	for e in ok:
		r -= float(e[1])
		if r <= 0.0:
			return e[0]
	return ok[-1][0]
