# Development status — MAN VS MACHINE

Last updated: 2026-10-22

## Checklist
- [x] Project setup: Godot 4.6, 640x360 integer-scaled viewport, nearest-neighbour filtering, GL Compatibility renderer, autoloads, full input map (P1 / P2 / gamepads)
- [x] Shared fighter state machine: walk forward/back, jump (with pre-jump), crouch, landing, facing, pushboxes, walls
- [x] Attack data: startup / active / recovery, damage, chip, hitstun, blockstun, knockback, hit level, knockdown, cancels, multi-hit, armour, invulnerability, movement, projectiles, telegraphs
- [x] Hit detection with hitboxes derived from the art, one hit per active window, trades, corner push-back
- [x] Blocking: hold back or the block button, standing vs crouching, chip damage, blockstun, block flash and sound
- [x] Hit-stop, screen shake, sparks, dust, light/heavy reactions, knockdown, get-up, KO slow-motion
- [x] Input buffer, motion commands (FF, QCF, QCB, DD, BF), chains/cancels, combo counter, damage scaling
- [x] Boxer: 29 animations including 3 specials and a super. 5 robots with distinct art, stats, movesets and AI
- [x] AI state machine (idle/approach/retreat/attack/defend/jump/recover/stunned/knocked down/defeated) with reaction delay and per-robot profiles
- [x] Match flow: intro, round call, FIGHT, timer, KO / time-up / draw, best-of-N, perfect, results
- [x] Arcade ladder, VS screen, defeat/retry, ending, high score saved; Versus 2P; Training mode; attract demo
- [x] 3 stages with parallax and animated details
- [x] HUD, pause menu (pauses the whole tree), settings (volumes, difficulty, timer, rounds, fullscreen, hitboxes), controls screen
- [x] Synthesized SFX and 4 music loops
- [x] Headless tests: load check, gameplay simulation, full flow
- [ ] Possible future work: throws, in-game key remapping, more animation frames, announcer voice

## Resuming work
- Asset pipeline: `tools/` (see README). Re-run `gen_data.py` after editing frame data.
- Run all three test scenes after changes (see README › Tests).
