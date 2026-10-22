shader_type canvas_item;
// Hit / block / armour flash: blends the sprite towards a solid colour.
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0);

void fragment() {
	// COLOR already holds texture * modulate here
	COLOR.rgb = mix(COLOR.rgb, flash_color.rgb, flash * 0.85);
}
