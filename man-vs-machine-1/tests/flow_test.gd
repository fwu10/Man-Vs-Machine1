extends Node
## (the scene node only spawns the driver below, which lives on the root so it
## survives scene changes)
## Real-time flow test: menu -> arcade VS screen -> fight -> pause/resume ->
## restart -> win every ladder match -> ending -> menu; plus versus/training.
## Run: godot --headless --path . res://tests/flow_test.tscn

var fails := 0


func ok(c: bool, what: String) -> void:
	if c:
		print("  ok: ", what)
	else:
		fails += 1
		printerr("  FAIL: ", what)


func scene_name() -> String:
	var s := get_tree().current_scene
	return s.scene_file_path.get_file() if s else ""


func wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, false, true).timeout


func _ready() -> void:
	if get_parent() != get_tree().root or get_tree().current_scene == self:
		var d: Node = load("res://tests/flow_test.gd").new()
		d.name = "FlowDriver"
		get_tree().root.add_child.call_deferred(d)
		return
	process_mode = Node.PROCESS_MODE_ALWAYS
	await wait(0.2)
	get_tree().change_scene_to_file(Game.SCENE_MENU)
	await wait(0.6)
	ok(scene_name() == "main_menu.tscn", "main menu loads")
	Game.start_arcade()
	await wait(1.0)
	ok(scene_name() == "vs_screen.tscn", "arcade opens the VS screen")
	await wait(5.0)
	ok(scene_name() == "fight.tscn", "VS screen auto-advances to the fight")
	var fight := get_tree().current_scene
	ok(fight.p2.data.id == "spark" and Game.stage_id == "industrial_arena", "first opponent SPARK on Industrial Arena")
	# pause / resume
	fight.pause_menu.open()
	await wait(0.2)
	var t0: int = fight.phase_frame
	await wait(0.5)
	ok(get_tree().paused and fight.phase_frame == t0, "pause freezes the match")
	fight.pause_menu.close()
	await wait(0.3)
	ok(not get_tree().paused and fight.phase_frame > t0, "resume continues the match")
	# restart
	fight.restart_match()
	await wait(1.0)
	ok(scene_name() == "fight.tscn" and get_tree().current_scene != fight, "restart reloads the fight")
	# win the ladder
	for i in Game.LADDER.size():
		fight = get_tree().current_scene
		if scene_name() != "fight.tscn":
			await wait(5.0)
			fight = get_tree().current_scene
		ok(scene_name() == "fight.tscn" and fight.p2.data.id == Game.LADDER[i], "ladder fight %d vs %s" % [i + 1, Game.LADDER[i]])
		fight.wins = [Settings.rounds_to_win, 0]
		fight._match_over()
		await wait(1.6)
		ok(fight.results.root.visible, "results screen shows after match %d" % (i + 1))
		var first: Button = fight.results.list.get_child(0)
		first.pressed.emit()
		await wait(1.0)
	ok(scene_name() == "ending.tscn", "beating OVERLORD shows the ending")
	Game.to_menu()
	await wait(0.8)
	ok(scene_name() == "main_menu.tscn", "ending returns to the menu")
	# defeat -> retry
	Game.start_arcade()
	await wait(6.0)
	fight = get_tree().current_scene
	fight.wins = [0, Settings.rounds_to_win]
	fight._match_over()
	await wait(1.6)
	ok(fight.results.title.text == "DEFEAT", "losing shows DEFEAT")
	fight.results.list.get_child(0).pressed.emit()
	await wait(1.0)
	ok(scene_name() == "fight.tscn" and get_tree().current_scene != fight, "RETRY FIGHT restarts")
	# training + versus
	Game.start_training("razor")
	await wait(1.0)
	fight = get_tree().current_scene
	ok(fight.training and fight.p2.data.id == "razor", "training mode loads with RAZOR dummy")
	Game.start_versus("volt")
	await wait(6.0)
	fight = get_tree().current_scene
	ok(scene_name() == "fight.tscn" and fight.p2.controller is PlayerController, "versus mode gives P2 keyboard control")
	Game.goto(Game.SCENE_SELECT)
	await wait(1.0)
	ok(scene_name() == "character_select.tscn", "character select loads")
	Game.to_menu()
	await wait(0.8)
	print("\n==== flow test: %d failures ====" % fails)
	get_tree().quit(1 if fails else 0)
