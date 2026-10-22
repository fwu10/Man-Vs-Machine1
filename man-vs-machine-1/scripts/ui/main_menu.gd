extends Control
## Title screen with Arcade / Versus / Training / Controls / Settings / Quit.
## Controls and Settings are sub-panels of this scene.

@onready var bg: Node2D = $Background
@onready var logo: TextureRect = $Logo
@onready var main_list: VBoxContainer = $MainList
@onready var controls_panel: Panel = $ControlsPanel
@onready var settings_panel: Panel = $SettingsPanel
@onready var footer: Label = $Footer

var _t := 0.0
var _hero: MenuActor
var _boss: MenuActor
var _sparks: Array[Dictionary] = []
var _settings_list: VBoxContainer
var _idle := 0.0


func _ready() -> void:
	theme = Game.theme
	Audio.play_music("menu")
	get_tree().paused = false
	Engine.time_scale = 1.0
	var stage: Node2D = load("res://scenes/stages/machine_core.tscn").instantiate()
	bg.add_child(stage)
	_hero = MenuActor.new()
	_hero.setup(Game.get_character("boxer"), "idle")
	_hero.position = Vector2(150, 318)
	_hero.scale = Vector2(1, 1)
	bg.add_child(_hero)
	_boss = MenuActor.new()
	_boss.setup(Game.get_character("overlord"), "idle", true)
	_boss.position = Vector2(500, 318)
	bg.add_child(_boss)
	_add(main_list, "ARCADE MODE", func(): Game.start_arcade())
	_add(main_list, "VERSUS (2P)", func(): Game.mode = "versus"; Game.goto(Game.SCENE_SELECT))
	_add(main_list, "TRAINING", func(): Game.mode = "training"; Game.goto(Game.SCENE_SELECT))
	_add(main_list, "CONTROLS", func(): _show(controls_panel))
	_add(main_list, "SETTINGS", func(): _show(settings_panel))
	_add(main_list, "QUIT", func(): get_tree().quit())
	footer.text = "HIGH SCORE %07d     (C) MAN VS MACHINE" % Settings.high_score
	_build_controls()
	_build_settings()
	controls_panel.visible = false
	settings_panel.visible = false
	main_list.get_child(0).grab_focus()


func _add(list: Container, text: String, cb: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.pressed.connect(func(): Audio.play_sfx("menu_select"); cb.call())
	b.focus_entered.connect(func(): Audio.play_sfx("menu_move", 0.0, -8.0))
	list.add_child(b)
	return b


func _show(panel: Panel) -> void:
	main_list.visible = false
	panel.visible = true
	var focus_target: Control = panel.find_children("*", "Button", true, false)[0]
	if panel == settings_panel and _settings_list.get_child_count() > 0:
		focus_target = _settings_list.get_child(0)
	focus_target.grab_focus()


func _back() -> void:
	Audio.play_sfx("menu_back")
	controls_panel.visible = false
	settings_panel.visible = false
	main_list.visible = true
	main_list.get_child(0).grab_focus()


func _input(event: InputEvent) -> void:
	if event is InputEventKey or event is InputEventJoypadButton or event is InputEventMouseButton:
		_idle = 0.0


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and not main_list.visible:
		_back()
		get_viewport().set_input_as_handled()


func _build_controls() -> void:
	var l := Label.new()
	l.position = Vector2(14, 10)
	l.text = """CONTROLS (KEYBOARD / GAMEPAD)

             PLAYER 1        PLAYER 2
MOVE         A / D           LEFT / RIGHT
JUMP         W               UP
CROUCH       S               DOWN
LIGHT PUNCH  J               NUM4 OR ,
HEAVY PUNCH  K               NUM5 OR .
LIGHT KICK   U               NUM1 OR M
HEAVY KICK   I               NUM2 OR /
BLOCK        L (OR HOLD BACK) NUM6 OR N
PAUSE        ESC / P

IRON COLE SPECIALS (FACING RIGHT)
IRON RUSH ........ > >  + HEAVY PUNCH
RISING HOOK ...... v >  + HEAVY PUNCH
KNOCKOUT STORM ... v v  + HEAVY PUNCH (POWER MAX)

HOLD BACK OR L TO BLOCK. CROUCH-BLOCK LOW ATTACKS,
STAND-BLOCK JUMP-INS. F1 SHOWS HITBOXES."""
	controls_panel.add_child(l)
	var b := Button.new()
	b.text = "BACK"
	b.position = Vector2(130, 262)
	b.pressed.connect(_back)
	controls_panel.add_child(b)


func _build_settings() -> void:
	_settings_list = VBoxContainer.new()
	_settings_list.position = Vector2(30, 40)
	_settings_list.size = Vector2(380, 230)
	_settings_list.add_theme_constant_override("separation", 6)
	settings_panel.add_child(_settings_list)
	var title := Label.new()
	title.text = "SETTINGS"
	title.position = Vector2(0, 8)
	title.size = Vector2(440, 20)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 18)
	settings_panel.add_child(title)
	_slider("MASTER", Settings.master_volume, func(v): Settings.master_volume = v)
	_slider("MUSIC", Settings.music_volume, func(v): Settings.music_volume = v)
	_slider("EFFECTS", Settings.sfx_volume, func(v): Settings.sfx_volume = v; Audio.play_sfx("punch_l"))
	_cycle("DIFFICULTY", func(): return Settings.DIFFICULTY_NAMES[Settings.difficulty],
		func(): Settings.difficulty = (Settings.difficulty + 1) % 3)
	_cycle("ROUND TIME", func(): return "INFINITE" if Settings.round_time == 0 else str(Settings.round_time),
		func():
			var i := Settings.ROUND_TIMES.find(Settings.round_time)
			Settings.round_time = Settings.ROUND_TIMES[(i + 1) % Settings.ROUND_TIMES.size()])
	_cycle("ROUNDS TO WIN", func(): return str(Settings.rounds_to_win),
		func(): Settings.rounds_to_win = 1 + (Settings.rounds_to_win % 3))
	_cycle("FULLSCREEN", func(): return "ON" if Settings.fullscreen else "OFF",
		func(): Settings.fullscreen = not Settings.fullscreen)
	_cycle("SHOW HITBOXES", func(): return "ON" if Settings.show_hitboxes else "OFF",
		func(): Settings.show_hitboxes = not Settings.show_hitboxes)
	var back := Button.new()
	back.text = "SAVE & BACK"
	back.pressed.connect(func(): Settings.save_settings(); _back())
	_settings_list.add_child(back)


func _slider(label: String, value: float, cb: Callable) -> void:
	var row := HBoxContainer.new()
	var l := Label.new()
	l.text = label
	l.custom_minimum_size = Vector2(150, 0)
	row.add_child(l)
	var s := HSlider.new()
	s.min_value = 0.0
	s.max_value = 1.0
	s.step = 0.05
	s.value = value
	s.custom_minimum_size = Vector2(200, 16)
	s.focus_mode = Control.FOCUS_ALL
	s.value_changed.connect(func(v): cb.call(v); Settings.apply())
	row.add_child(s)
	_settings_list.add_child(row)


func _cycle(label: String, getter: Callable, step: Callable) -> void:
	var b := Button.new()
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var refresh := func(): b.text = "%s: %s" % [label, getter.call()]
	refresh.call()
	b.pressed.connect(func(): step.call(); Settings.apply(); refresh.call(); Audio.play_sfx("menu_move"))
	b.focus_entered.connect(func(): Audio.play_sfx("menu_move", 0.0, -8.0))
	_settings_list.add_child(b)


func _process(delta: float) -> void:
	_t += delta
	_idle += delta
	if _idle > 25.0 and main_list.visible:
		_idle = -999.0
		Game.start_demo()   # attract mode after 25 s of no input
	logo.position.y = 4 + roundf(sin(_t * 2.0) * 3.0)
	# occasional robot "glare" and hero stance swap
	if fmod(_t, 6.0) < delta:
		_hero.play("intro")
	elif fmod(_t, 6.0) > 1.2 and _hero.anim == "intro":
		_hero.play("idle")
