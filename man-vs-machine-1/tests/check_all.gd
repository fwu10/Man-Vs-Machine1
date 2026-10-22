extends Node
## Headless smoke check: loads every script and scene in the project and
## reports anything that fails to load.
## Run: godot --headless --path . --script res://tests/check_all.gd

func _ready() -> void:
	var bad := 0
	var files: Array[String] = []
	_collect("res://scripts", files)
	_collect("res://scenes", files)
	for f in files:
		var r = load(f)
		if r == null or (r is GDScript and not r.can_instantiate()):
			printerr("FAILED: ", f)
			bad += 1
		elif r is PackedScene:
			var inst = r.instantiate()
			if inst == null:
				printerr("CANNOT INSTANTIATE: ", f)
				bad += 1
			else:
				inst.free()
	print("checked %d files, %d failures" % [files.size(), bad])
	get_tree().quit(1 if bad > 0 else 0)


func _collect(dir: String, out: Array[String]) -> void:
	var d := DirAccess.open(dir)
	if d == null:
		return
	for f in d.get_files():
		if f.ends_with(".gd") or f.ends_with(".tscn"):
			out.append(dir + "/" + f)
	for sub in d.get_directories():
		_collect(dir + "/" + sub, out)
