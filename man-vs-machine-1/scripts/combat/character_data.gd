class_name CharacterData
extends Resource
## Stats, art references, moves and AI profile for one fighter.
## Built from data/characters/<id>.json plus the generated sprite metadata
## assets/characters/<id>/<id>_anims.json.

@export var id: String = ""
@export var display_name: String = ""
@export var full_name: String = ""
@export var title: String = ""
@export var bio: String = ""
@export var is_robot: bool = true
@export var max_health: float = 1000.0
@export var walk_fwd: float = 2.2
@export var walk_back: float = 1.8
@export var jump_velocity: float = 8.4
@export var jump_x: float = 2.6
@export var gravity: float = 0.44
@export var weight: float = 1.0           ## divides received knockback
@export var theme_color: Color = Color.WHITE
@export var hit_sfx: String = "metal"     ## "flesh" for the human, "metal" for robots
@export var sheet: Texture2D
@export var portrait: Texture2D
@export var frame_size: Vector2i = Vector2i(144, 120)
@export var origin: Vector2i = Vector2i(72, 112)
@export var columns: int = 1
@export var rows: int = 1
@export var anims: Dictionary = {}        ## name -> {row, frames, fps, loop}
@export var hurt_stand: Rect2
@export var hurt_crouch: Rect2
@export var hurt_air: Rect2
@export var push_width: float = 28.0
@export var attacks: Dictionary = {}      ## id -> AttackData
@export var normals: Dictionary = {}      ## input slot ("lp", "c_hk", "j_lp"...) -> attack id
@export var specials: Array = []          ## [{attack, motion, button, meter}] in priority order
@export var ai: Dictionary = {}


static func load_from(cid: String) -> CharacterData:
	var c := CharacterData.new()
	c.id = cid
	var d: Dictionary = _read_json("res://data/characters/%s.json" % cid)
	var meta: Dictionary = _read_json("res://assets/characters/%s/%s_anims.json" % [cid, cid])
	c.display_name = d.get("name", cid.to_upper())
	c.full_name = d.get("full_name", c.display_name)
	c.title = d.get("title", "")
	c.bio = d.get("bio", "")
	c.is_robot = bool(d.get("robot", true))
	c.max_health = float(d.get("health", 1000))
	c.walk_fwd = float(d.get("walk_fwd", 2.2))
	c.walk_back = float(d.get("walk_back", 1.8))
	c.jump_velocity = float(d.get("jump_velocity", 8.4))
	c.jump_x = float(d.get("jump_x", 2.6))
	c.gravity = float(d.get("gravity", 0.44))
	c.weight = float(d.get("weight", 1.0))
	c.theme_color = Color(d.get("color", "#ffffff"))
	c.hit_sfx = d.get("hit_sfx", "metal")
	c.sheet = load("res://assets/characters/%s/%s_sheet.png" % [cid, cid])
	c.portrait = load("res://assets/characters/%s/%s_portrait.png" % [cid, cid])
	c.frame_size = Vector2i(int(meta.get("frame_w", 144)), int(meta.get("frame_h", 120)))
	c.origin = Vector2i(int(meta.get("origin_x", 72)), int(meta.get("origin_y", 112)))
	c.columns = int(meta.get("columns", 1))
	c.rows = int(meta.get("rows", 1))
	c.anims = meta.get("anims", {})
	c.hurt_stand = _rect(meta.get("hurt_stand", [-12, -90, 28, 90]))
	c.hurt_crouch = _rect(meta.get("hurt_crouch", [-12, -60, 28, 60]))
	c.hurt_air = _rect(meta.get("hurt_air", [-12, -80, 28, 70]))
	# pushbox a little wider than the hurtbox core so bodies do not visually interpenetrate
	c.push_width = float(meta.get("push_w", 28)) * 1.3
	var atk_d: Dictionary = d.get("attacks", {})
	for aid in atk_d:
		c.attacks[aid] = AttackData.from_dict(aid, atk_d[aid], c.anims)
	c.normals = d.get("normals", {})
	c.specials = d.get("specials", [])
	c.ai = d.get("ai", {})
	return c


static func _rect(a: Array) -> Rect2:
	return Rect2(a[0], a[1], a[2], a[3])


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("Missing data file: " + path)
		return {}
	var txt := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(txt)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Bad JSON in " + path)
		return {}
	return parsed
