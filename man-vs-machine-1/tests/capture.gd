extends Node
## Visual check helper: jumps straight into a CPU-vs-CPU fight (or another
## scene) so Movie Maker can record frames. Env: CAPTURE_OPP, CAPTURE_SCENE.

func _ready() -> void:
	var scene := OS.get_environment("CAPTURE_SCENE")
	await get_tree().process_frame
	if scene != "":
		get_tree().change_scene_to_file(scene)
		return
	var opp := OS.get_environment("CAPTURE_OPP")
	Game.demo = true
	Game.mode = "versus"
	Game.opponent_id = opp if opp != "" else "spark"
	Game.stage_id = Game.STAGE_FOR[Game.opponent_id]
	if OS.get_environment("CAPTURE_HITBOX") == "1":
		Settings.show_hitboxes = true
	get_tree().change_scene_to_file(Game.SCENE_FIGHT)
