extends CanvasLayer
## Pause menu: pauses the whole tree (fighters, AI, timers, effects) while
## this layer keeps processing. Dimmed overlay behind the buttons.

@onready var root: Control = $Root
@onready var list: VBoxContainer = $Root/Panel/List
@onready var title: Label = $Root/Panel/Title

var m: Node
var _move_list: Label


func setup(match_node: Node) -> void:
	m = match_node
	process_mode = Node.PROCESS_MODE_ALWAYS
	root.theme = Game.theme
	root.visible = false
	title.add_theme_font_size_override("font_size", 27)
	_add("RESUME", close)
	_add("RESTART MATCH", func(): Audio.play_sfx("menu_select"); m.restart_match())
	_add("MOVE LIST", _toggle_moves)
	_add("HITBOXES", func(): Settings.show_hitboxes = not Settings.show_hitboxes; _refresh())
	_add("MAIN MENU", func(): Audio.play_sfx("menu_back"); Game.to_menu())
	_move_list = Label.new()
	_move_list.visible = false
	_move_list.add_theme_font_size_override("font_size", 9)
	_move_list.text = _moves_text()
	$Root/Panel.add_child(_move_list)
	_move_list.position = Vector2(12, 200)


func _add(text: String, cb: Callable) -> void:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_ALL
	b.pressed.connect(cb)
	b.focus_entered.connect(func(): Audio.play_sfx("menu_move", 0.0, -6.0))
	list.add_child(b)


func _refresh() -> void:
	list.get_child(3).text = "HITBOXES: " + ("ON" if Settings.show_hitboxes else "OFF")


func _toggle_moves() -> void:
	_move_list.visible = not _move_list.visible


func _moves_text() -> String:
	return "IRON COLE - COMMANDS (facing right)\n" + \
		"IRON RUSH ....... > > + HEAVY PUNCH\n" + \
		"RISING HOOK ..... v > + HEAVY PUNCH\n" + \
		"KNOCKOUT STORM .. v v + HEAVY PUNCH (POWER MAX)\n" + \
		"CHAINS: LP>LP>HP  LK>HK  LP/LK>SPECIAL"


func open() -> void:
	if root.visible:
		close()
		return
	root.visible = true
	get_tree().paused = true
	_refresh()
	Audio.play_sfx("pause")
	list.get_child(0).grab_focus()


func close() -> void:
	root.visible = false
	_move_list.visible = false
	get_tree().paused = false


func _unhandled_input(event: InputEvent) -> void:
	if root.visible and (event.is_action_pressed("pause") or event.is_action_pressed("ui_cancel")):
		close()
		get_viewport().set_input_as_handled()
