class_name InputBuffer
extends RefCounted
## Rolling history of directions (numpad, relative to facing) and button
## presses. Provides buffered button presses and command-motion recognition.

const SIZE := 48
const PRESS_WINDOW := 6       ## a press stays usable for this many frames
const MOTION_TAIL := 9        ## last motion direction must be this recent

var _dirs: Array[int] = []
var _presses: Array[int] = []


func clear() -> void:
	_dirs.clear()
	_presses.clear()


func push(dir: int, pressed: int) -> void:
	_dirs.append(dir)
	_presses.append(pressed)
	if _dirs.size() > SIZE:
		_dirs.pop_front()
		_presses.pop_front()


## During hit-stop time is frozen: presses are merged into the newest frame
## so buffered follow-ups (combo cancels) don't expire while the game is frozen.
func merge_press(pressed: int) -> void:
	if _presses.is_empty():
		push(5, pressed)
	else:
		_presses[-1] |= pressed


## Age (0 = this frame) of the newest unconsumed press of any button in mask,
## or -1 if none inside the window.
func press_age(mask: int, window: int = PRESS_WINDOW) -> int:
	var n := _presses.size()
	for age in range(min(window, n)):
		if _presses[n - 1 - age] & mask:
			return age
	return -1


func consume(mask: int, window: int = PRESS_WINDOW) -> void:
	var n := _presses.size()
	for age in range(min(window, n)):
		_presses[n - 1 - age] &= ~mask


func current_dir() -> int:
	return 5 if _dirs.is_empty() else _dirs[-1]


## Run-length list of directions over the last max_age frames:
## each entry is [dir, newest_age, length], oldest first.
func _runs(max_age: int) -> Array:
	var runs: Array = []
	var n := _dirs.size()
	for i in range(max(0, n - max_age), n):
		var d := _dirs[i]
		var age := n - 1 - i
		if runs.is_empty() or runs[-1][0] != d:
			runs.append([d, age, 1])
		else:
			runs[-1][1] = age
			runs[-1][2] += 1
	return runs


## Checks a named motion ending shortly before (or at) press_age.
## Supported: FF (dash tap), BF, QCF (2-3-6), QCB (2-1-4), DD (double tap down).
func motion(name: String, press_at: int = 0) -> bool:
	var runs := _runs(30)
	if runs.size() < 2:
		return false
	# Ignore direction changes that happened after the button press.
	while runs.size() > 0 and runs[-1][1] + runs[-1][2] - 1 < press_at:
		runs.pop_back()
	if runs.is_empty():
		return false
	var last: Array = runs[-1]
	if last[1] - press_at > MOTION_TAIL:
		return false
	var i := runs.size() - 1
	match name:
		"FF", "DD", "BB":
			var d := 6 if name == "FF" else (2 if name == "DD" else 4)
			if last[0] != d or i < 2:
				return false
			var gap: Array = runs[i - 1]
			var first: Array = runs[i - 2]
			return gap[0] != d and gap[2] <= 10 and first[0] == d and first[2] <= 14 \
				and (name != "DD" or gap[0] in [5, 4, 6, 8])
		"QCF", "QCB":
			var fwd := 6 if name == "QCF" else 4
			var diag := 3 if name == "QCF" else 1
			if last[0] != fwd:
				return false
			var j := i - 1
			if j >= 0 and runs[j][0] == diag:
				j -= 1
			return j >= 0 and runs[j][0] in [2, 1 if name == "QCF" else 3] and runs[j][1] - press_at <= 20
		"BF":
			if last[0] != 6 or i < 1:
				return false
			var prev: Array = runs[i - 1]
			if prev[0] == 5 and i >= 2 and prev[2] <= 6:
				prev = runs[i - 2]
			return prev[0] in [4, 1, 7] and prev[1] - press_at <= 14
	return false
