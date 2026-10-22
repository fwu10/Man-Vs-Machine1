class_name AttackData
extends Resource
## One move's frame data. All timings are in 60 Hz game frames.
## Hitboxes are in fighter-local pixels for a fighter facing right
## (x forward, y up is negative, origin on the ground between the feet).

@export var id: String = ""
@export var anim: String = ""
@export var display_name: String = ""
@export var startup: int = 4
@export var active: int = 3
@export var recovery: int = 8
@export var damage: float = 30.0
@export var chip: float = 0.0             ## damage dealt through a block
@export var hitstun: int = 14
@export var blockstun: int = 10
@export var knockback: float = 3.0        ## push on hit (px/frame, decays)
@export var block_push: float = 2.5
@export var level: String = "mid"         ## high / mid / low / overhead
@export var strength: String = "light"    ## light / heavy (reaction + effects)
@export var knockdown: bool = false
@export var launch: Vector2 = Vector2(2.5, -5.0)   ## velocity applied on knockdown
@export var can_hit_air: bool = true
@export var blockable: bool = true
@export var hitstop: int = 6
@export var shake: float = 0.0
@export var sfx: String = "punch_l"
@export var cancel_into: PackedStringArray = PackedStringArray()   ## attack ids, or "special"/"super"
@export var hitbox: Rect2 = Rect2()        ## empty = no melee hitbox
@export var has_hitbox: bool = false
@export var anim_active: PackedInt32Array = PackedInt32Array()
@export var hits: int = 1
@export var hit_interval: int = 99
@export var invuln_until: int = 0          ## fully invulnerable up to this frame
@export var armor_until: int = 0           ## absorbs hits (no stun) up to this frame
@export var move: Array = []               ## [[from_frame, to_frame, vx], ...]
@export var air_launch: Vector3 = Vector3.ZERO   ## (frame, vx, vy): self-launch (uppercuts)
@export var projectile: Dictionary = {}    ## spawned at end of startup
@export var counter: bool = false          ## parry stance: active frames catch strikes
@export var counter_attack: String = ""
@export var teleport: bool = false
@export var is_special: bool = false
@export var is_super: bool = false
@export var meter_cost: float = 0.0
@export var air: bool = false
@export var fx: String = ""                ## visual: "beam", "charge", "electric"...
@export var telegraph: int = 0             ## frames of warning before the active phase


func total_frames() -> int:
	return startup + active + recovery


static func from_dict(aid: String, d: Dictionary, meta_anims: Dictionary) -> AttackData:
	var a := AttackData.new()
	a.id = aid
	a.anim = d.get("anim", aid)
	a.display_name = d.get("name", aid.to_upper())
	a.startup = int(d.get("startup", 4))
	a.active = int(d.get("active", 3))
	a.recovery = int(d.get("recovery", 8))
	a.damage = float(d.get("damage", 30))
	a.chip = float(d.get("chip", 0))
	a.hitstun = int(d.get("hitstun", 14))
	a.blockstun = int(d.get("blockstun", 10))
	a.knockback = float(d.get("knockback", 3.0))
	a.block_push = float(d.get("block_push", a.knockback * 0.8))
	a.level = d.get("level", "mid")
	a.strength = d.get("strength", "light")
	a.knockdown = bool(d.get("knockdown", false))
	if d.has("launch"):
		a.launch = Vector2(d["launch"][0], d["launch"][1])
	a.can_hit_air = bool(d.get("can_hit_air", true))
	a.blockable = bool(d.get("blockable", true))
	a.hitstop = int(d.get("hitstop", 10 if a.strength == "heavy" else 6))
	a.shake = float(d.get("shake", 3.0 if a.strength == "heavy" else 0.0))
	a.sfx = d.get("sfx", "punch_h" if a.strength == "heavy" else "punch_l")
	a.cancel_into = PackedStringArray(d.get("cancel", []))
	a.hits = int(d.get("hits", 1))
	a.hit_interval = int(d.get("hit_interval", 99))
	a.invuln_until = int(d.get("invuln", 0))
	a.armor_until = int(d.get("armor", 0))
	a.move = d.get("move", [])
	if d.has("air_launch"):
		var al = d["air_launch"]
		a.air_launch = Vector3(al[0], al[1], al[2])
	a.projectile = d.get("projectile", {})
	a.counter = bool(d.get("counter", false))
	a.counter_attack = d.get("counter_attack", "")
	a.teleport = bool(d.get("teleport", false))
	a.is_special = bool(d.get("special", false))
	a.is_super = bool(d.get("super", false))
	a.meter_cost = float(d.get("meter_cost", 100.0 if a.is_super else 0.0))
	a.air = aid.begins_with("j_")
	a.fx = d.get("fx", "")
	a.telegraph = int(d.get("telegraph", 0))
	# Hitbox: explicit override, otherwise the box derived from the art.
	var meta: Dictionary = meta_anims.get(a.anim, {})
	if d.has("hitbox"):
		var h = d["hitbox"]
		a.hitbox = Rect2(h[0], h[1], h[2], h[3])
		a.has_hitbox = true
	elif meta.has("hitbox") and not d.get("no_hitbox", false):
		var h2 = meta["hitbox"]
		a.hitbox = Rect2(h2[0], h2[1], h2[2], h2[3])
		a.has_hitbox = true
	if d.has("anim_active"):
		a.anim_active = PackedInt32Array(d["anim_active"])
	elif meta.has("active_frames"):
		a.anim_active = PackedInt32Array(meta["active_frames"])
	return a
