extends Control
## Arcade ending: the champion celebrates in the ruined Machine Core.

const LINES := [
	"THE CORE GOES DARK.",
	"",
	"ONE BY ONE THE ROBOT LEAGUES FALL SILENT.",
	"THE CROWDS RETURN TO THE OLD ARENAS -",
	"TO WATCH PEOPLE FIGHT AGAIN.",
	"",
	"MARCUS 'IRON' COLE NEVER RETIRED.",
	"SOMEBODY HAD TO KEEP THE BELT HUMAN.",
	"",
	"THANK YOU FOR PLAYING",
	"MAN VS MACHINE",
]

var _t := 0.0
var _hero: MenuActor
var _foe: MenuActor
var _sparks: Array[Dictionary] = []
var _new_record := false


func _ready() -> void:
	theme = Game.theme
	Audio.play_music("menu")
	Audio.play_sfx("victory")
	var st: Node2D = load("res://scenes/stages/machine_core.tscn").instantiate()
	add_child(st)
	move_child(st, 0)
	_hero = MenuActor.new()
	_hero.setup(Game.get_character("boxer"), "victory")
	_hero.position = Vector2(250, 318)
	add_child(_hero)
	_foe = MenuActor.new()
	_foe.setup(Game.get_character("overlord"), "knockdown", true)
	_foe.position = Vector2(450, 318)
	_foe.frame = Game.get_character("overlord").anims["knockdown"]["row"] * Game.get_character("overlord").columns + 3
	_foe.set_process(false)
	add_child(_foe)
	_new_record = Game.score >= Settings.high_score and Game.score > 0


func _process(delta: float) -> void:
	_t += delta
	if randf() < 0.3:
		_sparks.append({"p": Vector2(450 + randf_range(-40, 40), 300 + randf_range(-20, 10)), "v": Vector2(randf_range(-1, 1), randf_range(-2.5, -0.5)), "l": 40})
	for s in _sparks:
		s["p"] += s["v"]
		s["v"].y += 0.08
		s["l"] -= 1
	_sparks = _sparks.filter(func(s): return s["l"] > 0)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if _t > 2.0 and (event.is_action_pressed("ui_accept") or event.is_action_pressed("p1_lp")):
		Game.to_menu()


func _draw() -> void:
	for s in _sparks:
		draw_rect(Rect2(s["p"].floor(), Vector2(2, 2)), Color(1, 0.6, 0.2))
	draw_rect(Rect2(0, 0, 640, 150), Color(0, 0, 0, 0.55))
	PixelText.draw(self, Vector2(320, 34), "CHAMPION OF HUMANITY", 3, Color(1, 0.85, 0.3), Color(0.25, 0.05, 0), true)
	var shown := int(_t * 1.4)
	for i in mini(shown, LINES.size()):
		PixelText.draw(self, Vector2(320, 56 + i * 9), LINES[i], 1, Color(0.9, 0.92, 1), Color.BLACK, true)
	draw_rect(Rect2(170, 324, 300, 32), Color(0, 0, 0, 0.6))
	PixelText.draw(self, Vector2(320, 338), "FINAL SCORE %07d" % Game.score, 1, Color(1, 1, 0.7), Color.BLACK, true)
	var rec := "NEW HIGH SCORE!" if _new_record else "HIGH SCORE %07d" % Settings.high_score
	PixelText.draw(self, Vector2(320, 350), rec, 1, Color(1, 0.5, 0.3) if _new_record else Color(0.7, 0.8, 1), Color.BLACK, true)
