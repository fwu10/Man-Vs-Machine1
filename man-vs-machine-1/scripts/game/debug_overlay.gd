extends Node2D
## Development overlay (F1): hurtboxes (blue), active hitboxes (red),
## pushboxes (green), projectile boxes and the AI state.

var m: Node


func setup(match_node: Node) -> void:
	m = match_node


func _draw() -> void:
	if m == null or not Settings.show_hitboxes:
		return
	for f in [m.p1, m.p2]:
		for hr in f.get_hurtboxes():
			draw_rect(hr, Color(0.2, 0.5, 1.0, 0.25))
			draw_rect(hr, Color(0.3, 0.6, 1.0, 0.9), false, 1)
		var pb: Rect2 = f.get_pushbox()
		draw_rect(pb, Color(0.2, 1.0, 0.3, 0.7), false, 1)
		if f.is_hitbox_active():
			var hb: Rect2 = f.get_hitbox()
			draw_rect(hb, Color(1, 0.1, 0.1, 0.35))
			draw_rect(hb, Color(1, 0.2, 0.2, 1.0), false, 1)
		var info: String = Fighter.State.keys()[f.state]
		if f.atk:
			info += " %s %d/%d" % [f.atk.id, f.atk_frame, f.atk.total_frames()]
		if f.controller is AIController:
			info += " AI:" + f.controller.state_name()
		PixelText.draw(self, f.position + Vector2(-40, 14), info, 1, Color(1, 1, 0.6))
	for pr in m.projectiles_root.get_children():
		if pr.is_dangerous():
			var r: Rect2 = pr.get_hitbox()
			draw_rect(r, Color(1, 0.4, 0.1, 0.9), false, 1)
