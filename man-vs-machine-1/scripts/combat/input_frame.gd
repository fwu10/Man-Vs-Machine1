class_name InputFrame
extends RefCounted
## One frame of controller state, shared by human and AI controllers so both
## drive fighters through exactly the same rules.

const LP := 1
const HP := 2
const LK := 4
const HK := 8
const BUTTONS := {"lp": LP, "hp": HP, "lk": LK, "hk": HK}

var x: int = 0            ## absolute horizontal direction (-1 left, 1 right)
var up: bool = false
var down: bool = false
var pressed: int = 0      ## buttons pressed on this frame (bitmask)
var held: int = 0         ## buttons currently held (bitmask)
var block: bool = false   ## dedicated block button held
var request: String = ""  ## AI only: ask for a specific attack id (validated by Fighter)


## Numpad notation relative to facing: 6 = forward, 4 = back, 2 = down, 8 = up.
func numpad(facing: int) -> int:
	var rx := x * facing
	var col := 1 + rx            # 0 back, 1 neutral, 2 forward
	if up and not down:
		return 7 + col
	if down and not up:
		return 1 + col
	return 4 + col
