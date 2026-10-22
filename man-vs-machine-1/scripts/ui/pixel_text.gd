class_name PixelText
## Helpers for drawing the bitmap font with a hard 1px outline at integer scales.

const BASE := 9   ## native glyph height of the pixel font


static func width(text: String, scale: int) -> float:
	return text.length() * 6 * scale


static func draw(ci: CanvasItem, pos: Vector2, text: String, scale: int, color: Color,
		outline := Color(0, 0, 0, 1), centered := false) -> void:
	var f: Font = Game.font
	var size := BASE * scale
	var p := pos
	if centered:
		p.x -= width(text, scale) * 0.5
	p = p.round()
	if outline.a > 0:
		var o := scale
		for d in [Vector2(-o, 0), Vector2(o, 0), Vector2(0, -o), Vector2(0, o), Vector2(-o, -o), Vector2(o, o), Vector2(-o, o), Vector2(o, -o)]:
			ci.draw_string(f, p + d, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, outline)
	ci.draw_string(f, p, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)


## Draws a texture mirrored horizontally into rect r.
static func draw_flipped(ci: CanvasItem, tex: Texture2D, r: Rect2, modulate := Color.WHITE) -> void:
	ci.draw_set_transform(Vector2(r.end.x, r.position.y), 0.0, Vector2(-1, 1))
	ci.draw_texture_rect_region(tex, Rect2(Vector2.ZERO, r.size), Rect2(Vector2.ZERO, tex.get_size()), modulate)
	ci.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
