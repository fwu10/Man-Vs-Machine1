extends CanvasLayer
## End-of-match screen: victory / defeat / continue, depending on the mode.

@onready var root: Control = $Root
@onready var title: Label = $Root/Title
@onready var sub: Label = $Root/Sub
@onready var list: VBoxContainer = $Root/List

var m: Node


func setup(match_node: Node) -> void:
	m = match_node
	process_mode = Node.PROCESS_MODE_ALWAYS
	root.theme = Game.theme
	root.visible = false
	title.add_theme_font_size_override("font_size", 45)
	sub.add_theme_font_size_override("font_size", 18)


func show_results(p1_won: bool, wins: Array) -> void:
	await get_tree().create_timer(1.2).timeout
	root.visible = true
	for c in list.get_children():
		c.queue_free()
	match Game.mode:
		"arcade":
			if p1_won:
				var last := Game.ladder_index >= Game.LADDER.size() - 1
				title.text = "MACHINE DOWN!" if last else "VICTORY"
				title.add_theme_color_override("font_color", Color(1, 0.85, 0.25))
				sub.text = "SCORE %07d" % Game.score
				_add("FINAL STAGE" if last else "NEXT OPPONENT", func(): Game.arcade_match_won())
			else:
				title.text = "DEFEAT"
				title.add_theme_color_override("font_color", Color(1, 0.25, 0.2))
				sub.text = "THE MACHINES PREVAIL...  CONTINUE?"
				Game.score = 0
				_add("RETRY FIGHT", func(): m.restart_match())
				_add("RESTART ARCADE", func(): Game.start_arcade())
		"versus":
			title.text = "PLAYER %d WINS" % (1 if p1_won else 2)
			title.add_theme_color_override("font_color", Color(1, 0.85, 0.25))
			sub.text = "%d - %d" % [wins[0], wins[1]]
			_add("REMATCH", func(): m.restart_match())
			_add("CHANGE ROBOT", func(): Game.goto(Game.SCENE_SELECT))
		_:
			title.text = "MATCH OVER"
	_add("MAIN MENU", func(): Game.to_menu())
	await get_tree().process_frame
	list.get_child(0).grab_focus()


func _add(text: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.pressed.connect(func(): Audio.play_sfx("menu_select"); cb.call())
	b.focus_entered.connect(func(): Audio.play_sfx("menu_move", 0.0, -6.0))
	list.add_child(b)
