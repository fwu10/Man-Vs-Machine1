class_name MenuActor
extends Sprite2D
## Plays a character animation outside of combat (menus, VS screen, ending).

var data: CharacterData
var anim := "idle"
var _t := 0.0


func setup(cdata: CharacterData, anim_name := "idle", flip := false) -> void:
	data = cdata
	texture = data.sheet
	centered = false
	hframes = max(1, data.columns)
	vframes = max(1, data.rows)
	offset = Vector2(-data.origin.x, -data.origin.y)
	flip_h = flip
	play(anim_name)


func play(anim_name: String) -> void:
	anim = anim_name
	_t = 0.0
	_apply()


func _process(delta: float) -> void:
	if data == null:
		return
	_t += delta
	_apply()


func _apply() -> void:
	var a: Dictionary = data.anims.get(anim, data.anims.get("idle"))
	var n := int(a.get("frames", 1))
	var i := int(_t * float(a.get("fps", 8)))
	i = i % n if a.get("loop", false) else mini(i, n - 1)
	frame = int(a.get("row", 0)) * data.columns + i
