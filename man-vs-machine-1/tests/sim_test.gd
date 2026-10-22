extends Node
## Headless gameplay tests. Run:
##   godot --headless --path . res://tests/sim_test.tscn
## 1. font / data sanity
## 2. command-motion recognition (positive and negative cases)
## 3. scripted inputs: normals, specials, blocking, hit detection
## 4. full AI-vs-AI matches against every robot (round flow to MATCH_END)

var fails := 0
var checks := 0


class Scripted:
	extends RefCounted
	var frames: Array = []   ## each: {x, up, down, p (buttons), block}
	var i := 0

	func get_input(_f) -> InputFrame:
		var inp := InputFrame.new()
		if i < frames.size():
			var d: Dictionary = frames[i]
			inp.x = d.get("x", 0)
			inp.up = d.get("up", false)
			inp.down = d.get("down", false)
			inp.pressed = d.get("p", 0)
			inp.block = d.get("block", false)
		i += 1
		return inp


func ok(cond: bool, what: String) -> void:
	checks += 1
	if not cond:
		fails += 1
		printerr("  FAIL: ", what)
	else:
		print("  ok: ", what)


func _ready() -> void:
	await get_tree().process_frame
	test_data()
	test_motions()
	await test_scripted()
	await test_matches()
	print("\n==== %d checks, %d failures ====" % [checks, fails])
	get_tree().quit(1 if fails > 0 else 0)


func test_data() -> void:
	print("[data]")
	var sz := Game.font.get_string_size("FIGHT", HORIZONTAL_ALIGNMENT_LEFT, -1, 18)
	ok(sz.x > 50 and sz.y > 10, "pixel font measures text (%s)" % sz)
	for cid in ["boxer"] + Array(Game.ROSTER):
		var d := Game.get_character(cid)
		ok(d.sheet != null and d.attacks.size() >= 10, "%s loads sheet + %d attacks" % [cid, d.attacks.size()])
		for aid in d.attacks:
			var a: AttackData = d.attacks[aid]
			if not d.anims.has(a.anim):
				ok(false, "%s.%s anim '%s' exists" % [cid, aid, a.anim])
			if not a.has_hitbox and a.projectile.is_empty() and not a.counter and not a.teleport:
				ok(false, "%s.%s has a way to hit" % [cid, aid])
		for sp in d.specials:
			ok(d.attacks.has(sp["attack"]), "%s special %s defined" % [cid, sp["attack"]])
		if cid != "boxer":
			for key in ["close", "mid"]:
				for e in d.ai.get(key, []):
					ok(d.attacks.has(e[0]), "%s AI move %s exists" % [cid, e[0]])


func _feed(b: InputBuffer, seq: Array) -> void:
	for s in seq:
		b.push(s[0], s[1])


func test_motions() -> void:
	print("[motions]")
	var HP := InputFrame.HP
	var b := InputBuffer.new()
	_feed(b, [[5, 0], [6, 0], [6, 0], [5, 0], [5, 0], [6, 0], [6, HP]])
	ok(b.motion("FF", b.press_age(HP)), "6 5 6 + HP is a dash-punch (FF)")
	b.clear()
	_feed(b, [[5, 0], [6, 0], [6, 0], [6, 0], [6, 0], [6, 0], [6, HP]])
	ok(not b.motion("FF", b.press_age(HP)), "holding forward + HP is NOT FF")
	b.clear()
	_feed(b, [[5, 0], [2, 0], [2, 0], [3, 0], [3, 0], [6, 0], [6, HP]])
	ok(b.motion("QCF", b.press_age(HP)), "2 3 6 + HP is QCF")
	b.clear()
	_feed(b, [[5, 0], [2, 0], [2, 0], [6, HP]])
	ok(b.motion("QCF", b.press_age(HP)), "2 6 + HP (keyboard roll) is QCF")
	b.clear()
	_feed(b, [[2, 0], [2, 0], [2, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [5, 0], [6, 0], [6, HP]])
	ok(not b.motion("QCF", b.press_age(HP)), "crouch, stand still, then forward+HP is NOT QCF")
	b.clear()
	_feed(b, [[5, 0], [2, 0], [2, 0], [5, 0], [2, 0], [2, HP]])
	ok(b.motion("DD", b.press_age(HP)), "2 5 2 + HP is DD")
	b.clear()
	_feed(b, [[5, 0], [2, 0], [2, 0], [2, 0], [2, HP]])
	ok(not b.motion("DD", b.press_age(HP)), "holding down + HP is NOT DD")
	b.clear()
	_feed(b, [[5, 0], [2, 0], [1, 0], [4, 0], [4, HP]])
	ok(b.motion("QCB", b.press_age(HP)), "2 1 4 + HP is QCB")


## Builds a training-mode fight with scripted controllers and steps it manually.
func _make_fight(opp: String) -> Node:
	Game.mode = "versus"
	Game.opponent_id = opp
	Game.stage_id = Game.STAGE_FOR[opp]
	var fight: Node = load(Game.SCENE_FIGHT).instantiate()
	add_child(fight)
	fight.set_physics_process(false)
	fight.effects.set_physics_process(false)
	fight._begin_fight()
	return fight


func _step(fight: Node, n: int) -> void:
	for i in n:
		fight._physics_process(1.0 / 60.0)


func _hold(n: int, d: Dictionary) -> Array:
	var a := []
	for i in n:
		a.append(d.duplicate())
	return a


func test_scripted() -> void:
	print("[scripted combat]")
	var fight := _make_fight("spark")
	var p1: Fighter = fight.p1
	var p2: Fighter = fight.p2
	var s1 := Scripted.new()
	var s2 := Scripted.new()
	p1.controller = s1
	p2.controller = s2
	# walk forward
	var x0 := p1.position.x
	s1.frames = _hold(20, {"x": 1})
	s2.frames = _hold(400, {})
	_step(fight, 20)
	ok(p1.position.x > x0 + 30, "walk forward moves the boxer (%.1f -> %.1f)" % [x0, p1.position.x])
	# close the gap and jab
	p1.position.x = 300
	p2.position.x = 350
	s1.frames = [{"p": InputFrame.LP}] + _hold(20, {})
	s1.i = 0
	var hp_before := p2.health
	_step(fight, 12)
	ok(p2.health < hp_before, "jab at close range damages the robot (%.0f -> %.0f)" % [hp_before, p2.health])
	ok(p2.combo_taken >= 1 or p2.state == Fighter.State.HITSTUN or p2.state == Fighter.State.IDLE, "robot reacts to the jab")
	_step(fight, 30)
	# blocking: robot holds back (away from p1 = +x) while boxer heavy punches
	p1.position.x = 300
	p2.position.x = 345
	p2.health = p2.data.max_health
	s2.frames = _hold(60, {"x": 1})
	s2.i = 0
	fight.hitstop = 0
	s1.frames = [{"p": InputFrame.HP}] + _hold(40, {})
	s1.i = 0
	var blocked := false
	for i in 30:
		_step(fight, 1)
		if p2.state == Fighter.State.BLOCKSTUN:
			blocked = true
	ok(blocked and p2.health >= p2.data.max_health - 1, "holding back blocks the cross (health %.0f)" % p2.health)
	# low attack beats a standing block
	_step(fight, 30)
	p1.position.x = 300
	p2.position.x = 345
	s2.frames = _hold(60, {"x": 1})
	s2.i = 0
	s1.frames = [{"down": true, "p": InputFrame.LK}] + _hold(30, {"down": true})
	s1.i = 0
	var hb := p2.health
	_step(fight, 20)
	ok(p2.health < hb, "crouching low kick hits a standing-blocking robot")
	# specials via motion
	_step(fight, 40)
	p1.position.x = 260
	p2.position.x = 340
	s2.frames = _hold(100, {})
	s2.i = 0
	s1.frames = [{"x": 1}, {"x": 1}, {}, {}, {"x": 1}, {"x": 1, "p": InputFrame.HP}] + _hold(60, {})
	s1.i = 0
	var saw_rush := false
	for i in 30:
		_step(fight, 1)
		if p1.atk and p1.atk.id == "sp_rush":
			saw_rush = true
	ok(saw_rush, "> > + HP performs IRON RUSH")
	_step(fight, 60)
	p1.position.x = 260
	p2.position.x = 340
	s1.frames = [{"down": true}, {"down": true}, {"down": true, "x": 1}, {"x": 1, "p": InputFrame.HP}] + _hold(60, {})
	s1.i = 0
	var saw_hook := false
	for i in 30:
		_step(fight, 1)
		if p1.atk and p1.atk.id == "sp_hook":
			saw_hook = true
	ok(saw_hook, "v > + HP performs RISING HOOK")
	_step(fight, 80)
	# super with full meter
	p1.meter = 100.0
	p1.position.x = 280
	p2.position.x = 330
	p2.health = p2.data.max_health
	s1.frames = [{"down": true}, {"down": true}, {}, {"down": true}, {"down": true, "p": InputFrame.HP}] + _hold(90, {})
	s1.i = 0
	var saw_super := false
	for i in 90:
		_step(fight, 1)
		if p1.atk and p1.atk.id == "super":
			saw_super = true
	ok(saw_super and p1.meter < 50.0, "v v + HP at POWER MAX performs KNOCKOUT STORM")
	ok(p2.health < p2.data.max_health - 100, "super deals multi-hit damage (%.0f)" % p2.health)
	# chain: LP -> HP cancel on hit
	_step(fight, 80)
	p1.position.x = 300
	p2.position.x = 345
	s2.frames = _hold(100, {})
	s2.i = 0
	s1.frames = [{"p": InputFrame.LP}, {}, {}, {}, {}, {"p": InputFrame.HP}] + _hold(60, {})
	s1.i = 0
	var chained := false
	for i in 40:
		_step(fight, 1)
		if p1.atk and p1.atk.id == "hp" and p2.combo_taken >= 2:
			chained = true
	ok(chained, "LP -> HP chain combos (2 hits)")
	# jumping
	_step(fight, 60)
	s1.frames = [{"up": true}] + _hold(60, {})
	s1.i = 0
	var max_h := 0.0
	for i in 60:
		_step(fight, 1)
		max_h = maxf(max_h, Fighter.GROUND_Y - p1.position.y)
	ok(max_h > 50 and not p1.airborne, "jump arcs (%.0f px) and lands" % max_h)
	# fighters never overlap / leave the arena
	p1.position.x = 330
	p2.position.x = 331
	s1.frames = _hold(30, {"x": 1})
	s1.i = 0
	_step(fight, 30)
	ok(absf(p1.position.x - p2.position.x) >= (p1.data.push_width + p2.data.push_width) * 0.5 - 2, "pushboxes keep fighters apart")
	ok(p1.position.x >= Fighter.STAGE_LEFT and p2.position.x <= Fighter.STAGE_RIGHT, "fighters stay inside the stage")
	fight.queue_free()
	await get_tree().process_frame


func test_matches() -> void:
	print("[AI vs AI matches]")
	for opp in Game.ROSTER:
		var fight := _make_fight(opp)
		fight._set_phase(fight.Phase.ROUND_CALL)
		fight.p1.controls_enabled = false
		fight.p2.controls_enabled = false
		var prof: Dictionary = Game.get_character("spark").ai.duplicate(true)
		prof["mid"] = [["hk", 2], ["lk", 2], ["sp_rush", 1]]
		prof["far_specials"] = []
		prof["punish_moves"] = ["hp", "sp_rush", "hk"]
		prof["combos"] = {"lp": ["lp", "hp"], "c_lk": ["c_lk", "sp_rush"]}
		var boxer_ai := AIController.new(prof if OS.get_environment("MIRROR") == "1" else Game.get_character("boxer").ai, 0.6)
		boxer_ai.set_projectile_source(fight._projectiles_against)
		fight.p1.controller = boxer_ai
		var robot_ai := AIController.new(fight.p2.data.ai, 0.6)
		robot_ai.set_projectile_source(fight._projectiles_against)
		fight.p2.controller = robot_ai
		var frames := 0
		var counts := {"specials": 0, "p1_specials": 0}
		var states := {}
		fight.p2.attack_started.connect(func(_f, a): if a.is_special: counts["specials"] += 1)
		fight.p1.attack_started.connect(func(_f, a): if a.is_special: counts["p1_specials"] += 1)
		var dmg := [0.0, 0.0]
		var blocks := [0, 0]
		var hp := [fight.p1.health, fight.p2.health]
		while fight.phase != fight.Phase.MATCH_END and frames < 60 * 60 * 8:
			_step(fight, 1)
			frames += 1
			states[robot_ai.state_name()] = true
			for k in 2:
				var f: Fighter = fight.p1 if k == 0 else fight.p2
				if f.health < hp[k]:
					dmg[k] += hp[k] - f.health
				if f.state == Fighter.State.BLOCKSTUN and f.state_frame == 1:
					blocks[k] += 1
				hp[k] = f.health
		print("    damage taken: boxer %.0f robot %.0f | blocks: boxer %d robot %d" % [dmg[0], dmg[1], blocks[0], blocks[1]])
		var done: bool = fight.phase == fight.Phase.MATCH_END
		ok(done, "%s: match completes in %d frames, wins %s, rounds %d" % [opp, frames, fight.wins, fight.round_num])
		ok(counts["specials"] > 0, "%s: AI used specials (robot %d, boxer %d)" % [opp, counts["specials"], counts["p1_specials"]])
		ok(states.size() >= 5, "%s: AI visited states %s" % [opp, states.keys()])
		fight.queue_free()
		Engine.time_scale = 1.0
		await get_tree().process_frame
