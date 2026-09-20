# Player Motion 26.3 API Redesign

## Goal

Update Player Motion for Minecraft Java Edition 26.3, replace its public API with an ImpulseMotion-style storage interface, and retain the end-crystal explosion mechanism used by the `ender-crystal` branch.

## Scope

- Support only the new storage API. Remove `player_motion:api/launch_xyz`, `player_motion:api/launch_looking`, and the `player_motion.api.launch` objective.
- Accept every ImpulseMotion input field.
- Accumulate multiple calls made for the same target before the tick flush.
- Keep exactly three scoreboard objectives, one for each accumulated X, Y, and Z component.
- Keep the externally observable component range at `-1024.000000` through `1024.000000`.
- Target pack format 121.0 for Minecraft Java Edition 26.3.
- Do not adopt the enchantment-based motion mechanism.

## Public API

The caller writes a compound to `storage player_motion: in`, then invokes the private-looking public function tag `#player_motion:` as the entity that should receive motion.

```mcfunction
data modify storage player_motion: in set value {x:0.0,y:1.0,z:0.0,is_looking:false,is_vehicle_execution:false,is_knockback:false,is_explosion:false,multiplier:{elytra:0.5,swim:0.5,in_water:1.5}}
function #player_motion:
```

The tag is stored at `data/player_motion/tags/function/.json`. Its implementation function remains an internal detail.

Every call begins with these defaults and merges the caller's `in` compound over them:

```snbt
{
  x: 0.0,
  y: 0.0,
  z: 0.0,
  is_looking: false,
  is_vehicle_execution: false,
  is_knockback: false,
  is_explosion: false,
  multiplier: {
    elytra: 0.5,
    swim: 0.5,
    in_water: 1.5
  }
}
```

Defaults follow the ImpulseMotion implementation rather than its outdated README.

## Input Semantics

- `x`, `y`, and `z` are Motion components in blocks per tick.
- With `is_looking:false`, the components use global world axes.
- With `is_looking:true`, the components use the command execution rotation at the API call site.
- With `is_vehicle_execution:false`, a mounted target is rejected.
- With `is_vehicle_execution:true`, execution follows `on vehicle` recursively until the ridden root entity is reached, and that entity receives the motion.
- `is_knockback:true` multiplies this call's vector by `max(1 - knockback_resistance, 0)`.
- `is_explosion:true` multiplies this call's vector by `max(1 - explosion_knockback_resistance, 0)`.
- If both resistance flags are true, both factors apply in the same order as ImpulseMotion.
- `multiplier.in_water` scales all three components while the target is in water.
- `multiplier.elytra` scales only the positive forward component while the target is fall-flying.
- `multiplier.swim` scales only the positive forward component while the target is swimming.
- Multipliers and resistances apply only to the vector contributed by the current call. They never rescale motion accumulated by earlier calls.
- Spectator players and creative-mode players currently flying without fall-flying are rejected, matching ImpulseMotion behavior.

## Coordinate Transforms

The API first resolves `is_looking` against the command execution rotation to obtain a global vector. State-dependent forward-only multipliers are evaluated in the target entity's local coordinate system. The adjusted vector is then converted back to global X/Y/Z before accumulation.

Rotation capture uses the same design as ImpulseMotion: one marker with fixed UUID `[I;5636,369366532,369360896,5636]` in the empty `neac:` dimension. The marker exists only to capture command execution rotation safely. It is not involved in the explosion and is recreated or reused idempotently during load.

## Numeric Representation and Limits

New API arithmetic uses Minecraft 26.3 `compute ... float` expressions. The finalized contribution from each call is rounded to fixed point at `1 score = 0.000001 Motion` and stored in the three component objectives.

The three objectives are:

- `PlayerMotion.X`
- `PlayerMotion.Y`
- `PlayerMotion.Z`

Both the per-call result and the tick-accumulated result are saturated independently to `[-1,024,000,000, 1,024,000,000]`, corresponding to `[-1024.000000, 1024.000000]`. Adding two already-saturated values cannot overflow a signed 32-bit score because the temporary sum remains within `[-2,048,000,000, 2,048,000,000]`; the result is immediately saturated again before another call can add to it.

The six-decimal fixed-point representation preserves small contributions during scoreboard accumulation. It does not promise six-decimal physical accuracy after `float` calculations at large magnitudes. Around 1024, ordinary IEEE-754 float spacing is coarser than `0.000001`.

## Tick Accumulation

Each successful API call:

1. Calculates and saturates only that call's contribution.
2. Adds it to the target's `PlayerMotion.X`, `.Y`, and `.Z` scores.
3. Saturates the accumulated scores.
4. Adds an internal pending entity tag to the target.

The scheduled tick function processes every pending target once, uses the three accumulated scores to produce one end-crystal-based impulse, then clears the three scores and the pending tag. Fake-player scratch values may share the same three objectives; no fourth objective is introduced.

## End-Crystal Application

The end-crystal implementation remains based on the existing `ender-crystal` branch:

- Motion magnitude and direction are derived from the accumulated global X/Y/Z scores.
- Full-strength explosions and one residual-strength explosion are used as necessary.
- Explosion knockback resistance is temporarily neutralized only while the synthetic explosions are applied, because resistance was already handled by the public API flags.
- Player game mode is temporarily adjusted only where required by vanilla explosion behavior, then restored.
- Transient end crystals are summoned in the target's current execution dimension.
- The target and explosion execution position are moved relative to the original execution coordinates by `~ ~10000 ~`; this is not absolute Y=10000 and does not use the `neac:` dimension.
- The target is returned to the original execution coordinates within the same function execution.
- The synthetic crystals do not persist.

The explosion geometry and packet representation use double-precision vectors in 26.3. The `0.000001` scoreboard unit is therefore not blocked by the end-crystal mechanism itself; practical precision is primarily limited by the preceding float calculation and ordinary entity physics.

## Data-Pack Layout

- `data/player_motion/tags/function/.json`: sole public function-tag entry point.
- `data/player_motion/function/api/`: input normalization, eligibility checks, transforms, resistance handling, multiplier handling, saturation, and accumulation.
- `data/player_motion/function/internal/technical/`: load and scheduled tick orchestration.
- `data/player_motion/function/internal/rotation/`: fixed-marker rotation capture.
- `data/player_motion/function/internal/launch/`: conversion of accumulated scores into explosion parameters and target-state preservation.
- `data/player_motion/function/internal/summon/`: transient end-crystal spawning.
- `data/neac/dimension/.json`, `data/neac/dimension_type/void.json`, and `data/neac/function/load.mcfunction`: isolated rotation marker support.

Obsolete lookup-table trigonometry, old public launch functions, unused score objectives, and enchantment-based assets are removed rather than retained as compatibility shims.

## Failure and Edge-Case Behavior

- Calls from unsupported executors fail without adding pending motion.
- Zero vectors may be accumulated as zero but do not create an explosion during the flush.
- Missing fields use defaults; unknown fields are ignored.
- A missing `neac:` dimension is reported at load in the same manner as ImpulseMotion and prevents rotation-dependent processing from silently using a wrong rotation.
- Re-running load does not create duplicate fixed-UUID markers.
- Every flush restores temporary target state and clears pending state even when the accumulated vector is zero.

## Documentation

README examples use only `storage player_motion: in` and `function #player_motion:`. They document all input fields, implementation defaults, `0.000001` accumulation units, the `±1024` component limit, same-tick accumulation, vehicle behavior, and the fact that actual six-decimal accuracy is not guaranteed at large values because calculations use float.

## Verification

Static verification will check:

- pack format and JSON validity;
- exactly three `scoreboard objectives add` commands;
- absence of the old public functions and objective;
- presence of all public input fields and documented defaults;
- saturation constants and score scaling;
- the fixed UUID and `neac:` dimension resources;
- explosion execution in the target dimension at relative Y+10000;
- absence of enchantment motion assets.

Runtime verification on a Minecraft 26.3 server will cover global and looking-relative inputs, multiple calls before one flush, positive and negative components, `0.000001` accumulation, saturation at both limits, resistance flags, all three state multipliers, mounted-target behavior, spectator/creative-flight rejection, and cleanup after the explosion.
