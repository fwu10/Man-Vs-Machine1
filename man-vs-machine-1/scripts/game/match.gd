extends Node2D
## Runs a fight: round flow, timer, hit resolution between fighters and
## projectiles, hit-stop, screen shake, KO handling and match results.
## Fighters are advanced manually here (fixed 60 Hz order) so both sides
## are always resolved with identical rules.

enum Phase { INTRO, ROUND_CALL, FIGHT, ROUND_END, MATCH_END }

const FIGHTER_SCENE := preload("res://scenes/characters/fighter.tscn")
const PROJECTILE_SCRIPT := preload("res://scripts/combat/projectile.gd")
const START_X := [230.0, 410.0]

@onready var stage_root: Node2D = $StageRoot
@onready var fighters_root: Node2D = $Fighters
@onready var projectiles_root: Node2D = $Projectiles
@onready var effects: EffectsLayer = $Effects
@onready var debug_overlay: Node2D = $DebugOverlay
@onready var cam: Camera2D = $Camera
@onready var hud = $HUD
@onready var pause_menu = $PauseMenu
@onready var results = $Results

var p1: Fighter
var p2: Fighter
var stage: Node2D
var phase: Phase = Phase.INTRO
var phase_frame := 0
var round_num := 1
var wins := [0, 0]
var timer_frames := 0
var hitstop := 0
var shake := 0.0
var training := false
var dummy: DummyController
var round_winner := -1
var _ko_happened := false
var _slowmo := 0
var _time_over := false
var _boss := false
var _explosions := 0
var _training_idle := 0
var _last_combo_damage := 0.0
var _combo_damage := 0.0
var _round_damage := [0.0, 0.0]


func _ready() -> void:
	training = Game.mode == "training"
	_boss = Game.opponent_id == "overlord" and Game.mode == "arcade"
	_load_stage(Game.stage_id)
	p1 = _make_fighter(Game.PLAYER_ID, 0)
	p2 = _make_fighter(Game.opponent_id, 1)
	p1.opponent = p2
	p2.opponent = p1
	p1.controller = PlayerController.new("p1_")
	if Game.demo:
		var ai1 := AIController.new(p1.data.ai, 0.6)
		ai1.set_projectile_source(_projectiles_against)
		p1.controller = ai1
		var ai2 := AIController.new(p2.data.ai, 0.6)
		ai2.set_projectile_source(_projectiles_against)
		p2.controller = ai2
	elif Game.mode == "versus":
		p2.controller = PlayerController.new("p2_")
	elif training:
		dummy = DummyController.new()
		p2.controller = dummy
		p2.training_dummy = true
		p1.training_dummy = true
	else:
		var ai := AIController.new(p2.data.ai, Game.ai_difficulty())
		ai.set_projectile_source(_projectiles_against)
		p2.controller = ai
	hud.setup(p1, p2, self)
	debug_overlay.setup(self)
	pause_menu.setup(self)
	results.setup(self)
	Audio.play_music(Game.MUSIC_FOR_STAGE.get(Game.stage_id, "fight_industrial"))
	_reset_round()
	if training:
		_begin_fight()
		hud.announce("TRAINING", Color(0.5, 0.9, 1.0), 60, 3)
	elif Game.demo:
		_set_phase(Phase.ROUND_CALL)
		hud.demo = true
	else:
		_set_phase(Phase.INTRO)
		p1.play_intro()
		p2.play_intro()
		if _boss:
			hud.announce("WARNING", Color(1, 0.15, 0.1), 120, 4, true)
			Audio.play_sfx("alarm")


func _load_stage(sid: String) -> void:
	var path := "res://scenes/stages/%s.tscn" % sid
	if not ResourceLoader.exists(path):
		path = "res://scenes/stages/industrial_arena.tscn"
	stage = load(path).instantiate()
	stage_root.add_child(stage)


func _make_fighter(cid: String, idx: int) -> Fighter:
	var f: Fighter = FIGHTER_SCENE.instantiate()
	fighters_root.add_child(f)
	f.setup(Game.get_character(cid), idx)
	f.name = "P%d_%s" % [idx + 1, cid]
	f.attack_started.connect(_on_attack_started)
	f.projectile_requested.connect(_on_projectile_requested)
	f.effect_requested.connect(_on_effect)
	f.knocked_out.connect(_on_knocked_out)
	f.super_started.connect(_on_super)
	return f


func _reset_round() -> void:
	p1.reset_for_round(START_X[0], 1)
	p2.reset_for_round(START_X[1], -1)
	for pr in projectiles_root.get_children():
		pr.queue_free()
	effects.clear()
	timer_frames = Settings.round_time * 60 if Settings.round_time > 0 and not training else -1
	_ko_happened = false
	_time_over = false
	round_winner = -1
	_round_damage = [0.0, 0.0]
	hud.reset_round()


func _set_phase(ph: Phase) -> void:
	phase = ph
	phase_frame = 0


func _begin_fight() -> void:
	_set_phase(Phase.FIGHT)
	p1.controls_enabled = true
	p2.controls_enabled = true
	if p1.state == Fighter.State.INTRO:
		p1._set_state(Fighter.State.IDLE)
	if p2.state == Fighter.State.INTRO:
		p2._set_state(Fighter.State.IDLE)


# ------------------------------------------------------------------ main loop
func _physics_process(delta: float) -> void:
	phase_frame += 1
	match phase:
		Phase.INTRO:
			var intro_len := 170 if _boss else 100
			if phase_frame >= intro_len:
				_set_phase(Phase.ROUND_CALL)
		Phase.ROUND_CALL:
			if phase_frame == 1:
				var final: bool = wins[0] == Settings.rounds_to_win - 1 and wins[1] == Settings.rounds_to_win - 1
				hud.announce("FINAL ROUND" if final else "ROUND %d" % round_num, Color(1, 0.85, 0.3), 58, 3)
				Audio.play_sfx("bell")
			if phase_frame == 62:
				hud.announce("FIGHT!", Color(1, 0.3, 0.15), 40, 5)
				Audio.play_sfx("fight")
			if phase_frame >= 72:
				_begin_fight()
		Phase.FIGHT:
			if timer_frames > 0 and hitstop == 0:
				timer_frames -= 1
				if timer_frames == 0:
					_on_time_over()
		Phase.ROUND_END:
			_round_end_tick()
		Phase.MATCH_END:
			pass
	_step()
	_visuals(delta)
	if training:
		_training_tick()


func _step() -> void:
	var i1: InputFrame = p1.controller.get_input(p1)
	var i2: InputFrame = p2.controller.get_input(p2)
	if hitstop > 0:
		hitstop -= 1
		p1.record_only(i1)
		p2.record_only(i2)
		return
	if _slowmo > 0:
		_slowmo -= 1
		if _slowmo == 0:
			Engine.time_scale = 1.0
	p1.update_facing()
	p2.update_facing()
	p1.threat = _is_threat(p2, p1)
	p2.threat = _is_threat(p1, p2)
	p1.tick(i1)
	p2.tick(i2)
	_push_apart()
	for pr in projectiles_root.get_children():
		pr.tick()
	_resolve_hits()
	for pr in projectiles_root.get_children():
		if pr.dead:
			pr.queue_free()


func _visuals(delta: float) -> void:
	p1.visual_tick(delta)
	p2.visual_tick(delta)
	# depth: the attacking fighter draws on top
	if p1.is_attacking() and not p2.is_attacking():
		fighters_root.move_child(p1, 1)
	elif p2.is_attacking() and not p1.is_attacking():
		fighters_root.move_child(p2, 1)
	shake = maxf(0.0, shake * 0.86 - 0.05)
	cam.offset = Vector2(randf_range(-shake, shake), randf_range(-shake, shake)).round()
	if stage.has_method("set_focus"):
		stage.set_focus((p1.position.x + p2.position.x) * 0.5)
	hud.update_timer(timer_frames)
	debug_overlay.queue_redraw()


func _is_threat(attacker: Fighter, defender: Fighter) -> bool:
	var dist := absf(attacker.position.x - defender.position.x)
	if attacker.is_attacking() and attacker.atk and attacker.attack_phase() != "recovery":
		var reach := 0.0
		if attacker.atk.has_hitbox:
			reach = attacker.atk.hitbox.position.x + attacker.atk.hitbox.size.x
		if dist < reach + 60.0 or not attacker.atk.projectile.is_empty():
			return true
	for pr in projectiles_root.get_children():
		if pr.owner_fighter == attacker and not pr.dead:
			var dx: float = defender.position.x - pr.position.x
			if absf(dx) < 170 and (pr.kind == "orbital" or signf(dx) == signf(pr.vel.x)):
				return true
	return false


func _projectiles_against(f: Fighter) -> Array:
	var out := []
	for pr in projectiles_root.get_children():
		if pr.owner_fighter != f and not pr.dead:
			out.append(pr)
	return out


## Keeps the fighters from overlapping (pushboxes) while respecting walls.
func _push_apart() -> void:
	if p1.state == Fighter.State.KO or p2.state == Fighter.State.KO:
		return
	var a := p1.get_pushbox()
	var b := p2.get_pushbox()
	if not a.intersects(b):
		return
	var overlap := minf(a.end.x, b.end.x) - maxf(a.position.x, b.position.x)
	if overlap <= 0:
		return
	var dir := signf(p2.position.x - p1.position.x)
	if dir == 0:
		dir = float(p1.facing)
	var half := overlap * 0.5
	var p1x := p1.position.x - dir * half
	var p2x := p2.position.x + dir * half
	var lo := Fighter.STAGE_LEFT
	var hi := Fighter.STAGE_RIGHT
	# if one fighter is pinned against a wall, push the other one the whole way
	var p1min := lo + p1.data.push_width * 0.5
	var p1max := hi - p1.data.push_width * 0.5
	var p2min := lo + p2.data.push_width * 0.5
	var p2max := hi - p2.data.push_width * 0.5
	if p1x < p1min or p1x > p1max:
		p1x = clampf(p1x, p1min, p1max)
		p2x = p1x + dir * (p1.data.push_width + p2.data.push_width) * 0.5
	elif p2x < p2min or p2x > p2max:
		p2x = clampf(p2x, p2min, p2max)
		p1x = p2x - dir * (p1.data.push_width + p2.data.push_width) * 0.5
	p1.position.x = clampf(p1x, p1min, p1max)
	p2.position.x = clampf(p2x, p2min, p2max)


# ------------------------------------------------------------------ combat
func _resolve_hits() -> void:
	var events := []
	for pair in [[p1, p2], [p2, p1]]:
		var a: Fighter = pair[0]
		var d: Fighter = pair[1]
		if not a.is_hitbox_active() or not a.can_hit_now() or d.is_invulnerable():
			continue
		if d.airborne and not a.atk.can_hit_air:
			continue
		var hb := a.get_hitbox()
		for hr in d.get_hurtboxes():
			if hb.intersects(hr):
				var c := hb.intersection(hr).get_center()
				events.append([a, d, a.atk, c])
				break
	# apply simultaneously (trades are possible)
	for e in events:
		var a: Fighter = e[0]
		var d: Fighter = e[1]
		var atk: AttackData = e[2]
		var result := d.receive_hit(a, atk, a.position.x)
		if result == "parry":
			a.atk_hits = atk.hits
			hitstop = max(hitstop, 14)
			shake += 2.0
		else:
			a.on_attack_connected(result)
			_feedback(a, d, atk, result, e[3])
	# projectiles
	var prs := projectiles_root.get_children()
	for pr in prs:
		if not pr.is_dangerous():
			continue
		var target: Fighter = p2 if pr.owner_fighter == p1 else p1
		# projectile clashes
		for other in prs:
			if other != pr and other.owner_fighter != pr.owner_fighter and other.is_dangerous() \
					and pr.kind != "orbital" and other.kind != "orbital" and pr.get_hitbox().intersects(other.get_hitbox()):
				pr.dead = true
				other.dead = true
				effects.spawn("hit_h", (pr.position + other.position) * 0.5)
				Audio.play_sfx("zap")
		if pr.dead or target.is_invulnerable():
			continue
		if target.airborne and not pr.attack.can_hit_air:
			continue
		var hb2: Rect2 = pr.get_hitbox()
		for hr in target.get_hurtboxes():
			if hb2.intersects(hr):
				var from_x: float = pr.position.x - signf(pr.vel.x) * 40.0 if pr.vel.x != 0 else pr.owner_fighter.position.x
				var result2 := target.receive_hit(pr.owner_fighter, pr.attack, from_x)
				pr.on_hit()
				if pr.owner_fighter.is_attacking():
					pr.owner_fighter.atk_connected = true
				_feedback(pr.owner_fighter, target, pr.attack, result2, hb2.intersection(hr).get_center())
				break


func _feedback(a: Fighter, d: Fighter, atk: AttackData, result: String, at: Vector2) -> void:
	var face := a.facing
	match result:
		"hit":
			hitstop = max(hitstop, atk.hitstop)
			shake += atk.shake
			effects.spawn("hit_h" if atk.strength == "heavy" else "hit_l", at, face)
			Audio.play_sfx(atk.sfx)
			if d.data.is_robot:
				effects.spawn("metal", at, face)
				Audio.play_sfx("metal_h" if atk.strength == "heavy" else "metal_l", 0.1, -4.0)
			else:
				Audio.play_sfx("flesh_h" if atk.strength == "heavy" else "flesh_l", 0.1, -3.0)
			if d.combo_taken >= 2:
				hud.show_combo(a.player_index, d.combo_taken)
			var dmg := atk.damage
			_round_damage[a.player_index] += dmg
			_combo_damage = _combo_damage + dmg if d.combo_taken > 1 else dmg
			if a == p1 and Game.mode == "arcade":
				Game.score += int(dmg * 10) + (d.combo_taken - 1) * 50
			# corner pushback: the attacker slides back instead
			if d.at_wall() and not d.airborne:
				a.vel.x = -face * atk.knockback * 0.7
		"block":
			hitstop = max(hitstop, 5)
			effects.spawn("block", at, face)
			Audio.play_sfx("block")
			if d.at_wall():
				a.vel.x = -face * atk.block_push * 0.8
		"armor":
			hitstop = max(hitstop, 8)
			shake += 2.0
			effects.spawn("metal", at, face)
			Audio.play_sfx("armor")


func _on_attack_started(f: Fighter, a: AttackData) -> void:
	if a.fx == "beam":
		effects.spawn("beam", f.position, f.facing, {"owner": f, "life": a.total_frames() + 10})
		Audio.play_sfx("charge")
	elif a.fx == "charge":
		effects.spawn("charge", f.position, f.facing, {"owner": f, "life": a.startup})
		Audio.play_sfx("charge")
	elif a.fx == "electric":
		effects.spawn("electric", f.position, f.facing, {"owner": f, "life": a.total_frames()})
		Audio.play_sfx("zap")
	if a.telegraph > 0:
		Audio.play_sfx("alarm", 0.0, -6.0)


func _on_projectile_requested(f: Fighter, a: AttackData) -> void:
	var spec := a.projectile
	var count := int(spec.get("count", 1))
	for i in count:
		var pr: Projectile = PROJECTILE_SCRIPT.new()
		var xo := INF
		if spec.get("kind", "") == "orbital" and count > 1:
			xo = clampf(f.opponent.position.x + (i - (count - 1) * 0.5) * float(spec.get("spacing", 70)), 30, 610)
		pr.configure(f, a, spec, xo)
		pr.delay += i * int(spec.get("stagger", 0))
		pr.life += i * int(spec.get("stagger", 0))
		projectiles_root.add_child(pr)
	Audio.play_sfx(spec.get("sfx", "zap"))


func _on_effect(kind: String, pos: Vector2, facing: int) -> void:
	match kind:
		"beam", "charge", "electric":
			pass    # spawned from _on_attack_started with an owner reference
		_:
			effects.spawn(kind, pos, facing)


func _on_super(f: Fighter) -> void:
	hitstop = max(hitstop, 26)
	Game.flash_screen(Color(1, 1, 1, 0.6), 0.3)
	hud.super_flash(f.player_index, f.atk.display_name if f.atk else "SUPER")
	Audio.play_sfx("super")


# ------------------------------------------------------------------ round flow
func _on_knocked_out(f: Fighter) -> void:
	if training:
		return
	if phase != Phase.FIGHT and phase != Phase.ROUND_END:
		return
	var loser := f.player_index
	if phase == Phase.ROUND_END:
		if not _ko_happened:
			return
		round_winner = -1      # double KO in the same frame window = draw
		return
	_ko_happened = true
	round_winner = 1 - loser
	_end_round()
	Engine.time_scale = 0.35
	_slowmo = 40
	shake += 6.0
	Game.flash_screen(Color(1, 1, 1, 0.8), 0.4)
	effects.spawn("ko", f.position + Vector2(0, -60), f.facing)
	hud.announce("K.O.", Color(1, 0.2, 0.15), 110, 6, true)
	Audio.play_sfx("ko")
	if f.data.is_robot:
		_explosions = 50 if f.data.id == "overlord" else 18


func _on_time_over() -> void:
	_time_over = true
	var h1 := p1.health / p1.data.max_health
	var h2 := p2.health / p2.data.max_health
	if absf(h1 - h2) < 0.001:
		round_winner = -1
	else:
		round_winner = 0 if h1 > h2 else 1
	_end_round()
	hud.announce("TIME", Color(1, 0.85, 0.3), 100, 5)
	Audio.play_sfx("bell")


func _end_round() -> void:
	_set_phase(Phase.ROUND_END)
	p1.controls_enabled = false
	p2.controls_enabled = false


func _round_end_tick() -> void:
	if _explosions > 0 and phase_frame % 3 == 0:
		_explosions -= 1
		var robot := p2 if p2.data.is_robot and p2.state == Fighter.State.KO else p1
		var pos := robot.position + Vector2(randf_range(-30, 30), randf_range(-100, -10))
		effects.spawn("explosion" if robot.data.id == "overlord" else "metal", pos, robot.facing)
		if phase_frame % 9 == 0:
			Audio.play_sfx("explode" if robot.data.id == "overlord" else "metal_l")
			shake += 1.5
	if phase_frame == 150:
		if round_winner >= 0:
			wins[round_winner] += 1
			var w := p1 if round_winner == 0 else p2
			var l := p2 if round_winner == 0 else p1
			w.set_result_pose(true)
			l.set_result_pose(false)
			hud.set_wins(wins)
			var txt := "%s WINS" % w.data.display_name
			if w.health >= w.data.max_health:
				txt = "PERFECT!"
				if w == p1 and Game.mode == "arcade":
					Game.score += 5000
			hud.announce(txt, w.data.theme_color.lightened(0.3), 90, 3)
			if w == p1 and Game.mode == "arcade":
				Game.score += int(p1.health) * 5 + max(0, timer_frames / 60) * 100
		else:
			p1.set_result_pose(false)
			p2.set_result_pose(false)
			hud.announce("DRAW", Color(0.8, 0.8, 0.9), 90, 4)
	if phase_frame >= 260:
		var need := Settings.rounds_to_win
		if wins[0] >= need or wins[1] >= need or round_num >= need * 2 + 1:
			_match_over()
		else:
			round_num += 1
			_reset_round()
			_set_phase(Phase.ROUND_CALL)


func _match_over() -> void:
	_set_phase(Phase.MATCH_END)
	if Game.demo:
		await get_tree().create_timer(2.0).timeout
		Game.to_menu()
		return
	var p1_won: bool = wins[0] > wins[1]
	if Game.mode == "arcade":
		Audio.stop_music()
		Audio.play_sfx("victory" if p1_won else "defeat")
	results.show_results(p1_won, wins)


# ------------------------------------------------------------------ training
func _training_tick() -> void:
	p2.meter = 100.0
	p1.meter = maxf(p1.meter, 0.0)
	if p1.is_actionable() and (p2.is_actionable() or p2.state == Fighter.State.AIR):
		_training_idle += 1
		if _training_idle == 50:
			if p2.health < p2.data.max_health or p1.health < p1.data.max_health:
				p2.health = p2.data.max_health
				p1.health = p1.data.max_health
				p1.health_changed.emit(p1)
				p2.health_changed.emit(p2)
			p1.meter = 100.0
	else:
		_training_idle = 0
	hud.training_info(dummy.mode_name() if dummy else "", _combo_damage, p2.combo_taken)


func _unhandled_input(event: InputEvent) -> void:
	if Game.demo and (event is InputEventKey or event is InputEventJoypadButton) and event.is_pressed():
		Game.to_menu()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("debug_hitboxes"):
		Settings.show_hitboxes = not Settings.show_hitboxes
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("training_reset") and training and dummy:
		dummy.next_mode()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("pause") and phase != Phase.MATCH_END:
		pause_menu.open()
		get_viewport().set_input_as_handled()


func restart_match() -> void:
	Engine.time_scale = 1.0
	get_tree().paused = false
	Game.retry_match()
