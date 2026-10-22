class_name PlayerController
extends RefCounted
## Reads a human player's input actions ("p1_*" or "p2_*") into an InputFrame.
## Actions are defined in the project's Input Map so they can be remapped.

var prefix := "p1_"


func _init(p := "p1_") -> void:
	prefix = p


func get_input(_f: Fighter) -> InputFrame:
	var i := InputFrame.new()
	var l := Input.is_action_pressed(prefix + "left")
	var r := Input.is_action_pressed(prefix + "right")
	i.x = int(r) - int(l)          # left + right together cancel out
	i.up = Input.is_action_pressed(prefix + "up")
	i.down = Input.is_action_pressed(prefix + "down")
	if i.up and i.down:
		i.up = false
	i.block = Input.is_action_pressed(prefix + "block")
	for b in InputFrame.BUTTONS:
		var bit: int = InputFrame.BUTTONS[b]
		if Input.is_action_just_pressed(prefix + b):
			i.pressed |= bit
		if Input.is_action_pressed(prefix + b):
			i.held |= bit
	return i
