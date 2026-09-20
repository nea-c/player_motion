# Numbered Function Layout Design

## Goal

Reorganize the Player Motion function tree so its execution order is visible from file names, following the style of ImpulseMotion. Separate the public accumulation pipeline from the scheduled end-crystal application pipeline, while preserving all existing behavior and the public storage/tag API.

## Public Interface

The external API remains:

1. Write input to `storage player_motion: in`.
2. Run `function #player_motion:` as the target entity.

The public function tag will contain only `player_motion:accumulate/0`. Direct calls to old `player_motion:api/**` or `player_motion:internal/**` paths are unsupported. No compatibility wrappers will remain.

## Root Functions

The function root contains only orchestration functions and the two phase directories:

```text
function/
|-- load.mcfunction
|-- schedule_tick.mcfunction
|-- accumulate/
`-- apply/
```

`load.mcfunction` initializes `storage player_motion: _`, creates the three existing objectives, and starts the loop with:

```mcfunction
schedule function player_motion:schedule_tick 1t replace
```

`schedule_tick.mcfunction` first reschedules itself using the same `1t replace` command, then uses global player anchors to call `player_motion:apply/0.flush` once for each loaded dimension containing a player. The pack does not register a `minecraft:tick` function tag.

## Accumulation Pipeline

The immediate public-call pipeline is:

```text
accumulate/
|-- 0.mcfunction
|-- 1.call.mcfunction
|-- 2.explosion.mcfunction
|-- 2.knockback.mcfunction
|-- 3.looking.mcfunction
|-- 4.motion_set.mcfunction
|-- 5.score.mcfunction
|-- multiplier/
|   |-- elytra.mcfunction
|   |-- in_water.mcfunction
|   `-- swim.mcfunction
`-- rotation/
    |-- 0.get.mcfunction
    |-- 1.execution.mcfunction
    `-- 2.target.mcfunction
```

- `0` is the sole public function-tag target. It normalizes the input and captures the invocation rotation before delegating to `1.call`.
- `1.call` validates the target, performs vehicle redirection, applies optional resistance processing, selects looking-relative or global input, and advances the call through motion conversion and score accumulation.
- Both `2` functions apply their corresponding resistance before the optional `3.looking` transform, matching the visible numeric order and ImpulseMotion. Resistance is a uniform scalar, so the intended vector is unchanged; normal float-level rounding may differ because multiplication now occurs before rotation.
- `3.looking` converts invocation-relative input into a global vector.
- `4.motion_set` captures target rotation, converts the global vector into target-local coordinates, invokes applicable unnumbered multiplier helpers, and converts the result back to global coordinates.
- `5.score` clamps, converts, saturates, and accumulates the six-decimal fixed-point score components, then adds `player_motion.pending`.
- `multiplier/` is an unordered set of state-specific helpers and intentionally has no numeric prefix.
- `rotation/` uses numbers for its fixed-marker helper sequence.

## Application Pipeline

The scheduled end-crystal phase is:

```text
apply/
|-- 0.flush.mcfunction
|-- 1.launch.mcfunction
|-- 2.protect.mcfunction
|-- 3.prepare.mcfunction
|-- 4.apply.mcfunction
|-- 5.restore_invulnerable.mcfunction
|-- 6.cleanup.mcfunction
|-- gamemode/
|   |-- 0.get.mcfunction
|   `-- 1.restore.mcfunction
|-- passenger/
|   |-- 0.prepare_tree.mcfunction
|   |-- 1.resistance.mcfunction
|   |-- 2.prepare_boost.mcfunction
|   |-- 3.boost.mcfunction
|   |-- 4.protect_tree.mcfunction
|   |-- 5.protect_nonplayer.mcfunction
|   `-- 6.restore_tree.mcfunction
`-- summon/
    |-- 0.main.mcfunction
    |-- 1.crystal.mcfunction
    `-- 2.loop.mcfunction
```

- `0.flush` finds pending targets in its execution dimension, calls `1.launch`, always calls `6.cleanup`, and retries deferred invulnerability restoration.
- `1.launch` revalidates the current target, handles the passenger tree, invokes root protection, prepares the explosion geometry, applies the impulse, and restores temporary state.
- `2.protect` protects nonplayer roots and compensates for Motion clipped by the NBT write.
- `3.prepare` converts accumulated score values into end-crystal geometry.
- `4.apply` handles temporary player gamemodes, the relative Y+10000 teleport, crystal summoning, position restoration, and passenger launch state.
- `5.restore_invulnerable` restores only safe tagged entities and remains callable both immediately and from later scheduled passes.
- `6.cleanup` resets all three scores and removes `player_motion.pending`, including after early returns from launch.
- `gamemode/`, `passenger/`, and `summon/` keep their own numbered execution order.

The unused `internal/launch/exp_pos.mcfunction` is deleted.

## Registration and References

`data/minecraft/tags/function/load.json` continues to load `neac:load` and changes the Player Motion entry to `player_motion:load`.

`data/player_motion/tags/function/.json` changes its sole value to `player_motion:accumulate/0`.

Every internal `function player_motion:...`, scheduled function, and macro function reference is rewritten to the new path. The `api/` and `internal/` directories are removed after all references migrate.

## Behavioral Constraints

This change is structural except for the explicitly documented resistance/rotation evaluation order. It must preserve:

- all storage input fields and defaults;
- exactly three scoreboard objectives;
- six-decimal score accumulation and component saturation;
- same-tick accumulation followed by one scheduled flush;
- execution-relative and target-relative transforms;
- resistance and state multipliers;
- vehicle and full passenger-tree behavior;
- temporary gamemode and invulnerability restoration;
- end-crystal application at relative Y+10000 in the execution dimension;
- the ImpulseMotion-identical `neac` namespace.

## Verification

Tests will be changed before production paths move and will verify:

- the exact expected numbered function tree;
- the public tag points only to `player_motion:accumulate/0`;
- the load tag points to `player_motion:load`;
- both root functions use `player_motion:schedule_tick 1t replace` as specified;
- no `minecraft:tick` tag is introduced;
- every local Player Motion function reference resolves to a real file;
- no `api/`, `internal/`, or obsolete function path remains;
- the unused `exp_pos` helper is absent;
- all existing behavioral contracts still pass;
- the data pack loads and reloads successfully on Minecraft Java Edition 26.3.
