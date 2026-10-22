class_name DummyController
extends RefCounted
## Training-mode opponent: stands, crouches, jumps or guards on command.

enum Mode { STAND, CROUCH, BLOCK, CROUCH_BLOCK, JUMP }
const NAMES := ["STAND", "CROUCH", "GUARD (HIGH)", "GUARD (LOW)", "JUMP"]

var mode: Mode = Mode.STAND


func next_mode() -> void:
	mode = ((mode + 1) % Mode.size()) as Mode


func mode_name() -> String:
	return NAMES[mode]


func get_input(f: Fighter) -> InputFrame:
	var i := InputFrame.new()
	match mode:
		Mode.CROUCH:
			i.down = true
		Mode.BLOCK:
			i.block = true
		Mode.CROUCH_BLOCK:
			i.block = true
			i.down = true
		Mode.JUMP:
			i.up = f.is_actionable()
	return i
