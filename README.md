# Player Motion for Minecraft Java 26.3

An additive motion library using end-crystal impulses. This edition requires Minecraft Java **26.3**, data pack format **121**, including its float `compute` commands. Install the `player_motion` folder in your world's `datapacks` directory and restart the world/server so the `neac:` helper dimension is generated. `/reload` refreshes functions after installation.

## Calling the API

Set `storage player_motion: in`, then invoke `function #player_motion:` **as the target entity**. The call queues motion; the scheduled flush applies it. Components are measured in blocks per tick and add to existing velocity.

For global XYZ motion, run these commands in a function executed as your target:

```mcfunction
data modify storage player_motion: in set value {x:0.05,y:1.2,z:-0.3125}
function #player_motion:
```

For one block per tick along the invocation's facing direction:

```mcfunction
data modify storage player_motion: in set value {z:1.0,is_looking:true}
function #player_motion:
```

Use `execute as <target> at @s run function <your_function>` when you want the target's position and facing. `is_looking` uses the command rotation at invocation, including any `execute rotated` override. Local X is left, local Y is up, and local Z is forward. Global mode uses world axes.

The complete input with defaults is:

```snbt
{x:0.0,y:0.0,z:0.0,is_looking:false,is_vehicle_execution:false,is_knockback:false,is_explosion:false,multiplier:{elytra:0.5,swim:0.5,in_water:1.5}}
```

| Field | Meaning |
| --- | --- |
| `x`, `y`, `z` | Requested additive components; omitted components are zero. |
| `is_looking` | Interpret the vector in the invocation's local coordinates when true; otherwise use global XYZ. |
| `is_vehicle_execution` | When mounted, true routes recursively to the root vehicle; false rejects the call. The invocation's facing is preserved. |
| `is_knockback` | Multiply this call's XYZ by `max(1 - knockback_resistance, 0)`. |
| `is_explosion` | Multiply this call's XYZ by `max(1 - explosion_knockback_resistance, 0)`. |
| `multiplier.in_water` | Scale all XYZ components when the final target is in water; default 1.5. |
| `multiplier.elytra` | Scale only positive target-local Z when the final target is fall-flying; default 0.5. |
| `multiplier.swim` | Scale only positive target-local Z when the final target is swimming; default 0.5. |

All fields are optional. Missing multiplier entries retain their defaults. Use numeric values for vector components and multipliers, and boolean values for flags. Set the whole input compound for each call to avoid carrying earlier caller-supplied fields forward. The library copies the compound without changing it; `storage player_motion: _` is internal scratch space.

Both resistance flags default to false. When both are true, explosion resistance is applied first, then knockback resistance, so their factors multiply. A missing attribute contributes zero resistance. Next, the vector is transformed into the final target's local coordinates, water/elytra/swim factors are applied in that order, and it is transformed back to global XYZ. Zero and negative local Z are unchanged by elytra/swim factors. These transformations affect only the current call, not earlier queued motion.

Spectators and players using creative flight are rejected at call time. Creative players who are not flying may use the API. Mounted callers need `is_vehicle_execution:true`; the final root vehicle receives the motion and its state/attributes determine scaling. The root target is protected from the synthetic explosion as described below.

The root's full passenger tree is protected during the temporary teleport. Nonplayer passengers use temporary invulnerability; survival/adventure player passengers temporarily enter creative and then regain their original mode, while already-creative passengers keep it. Scoped explosion-resistance modifiers compensate for existing modifiers and verify full effective resistance wherever that attribute exists. If full resistance cannot be established (for example, an existing -1 total multiplier), the queued launch is skipped before protection, teleporting, or exploding; temporary modifiers are removed and the root and riders keep their prior motion and modes. Unrelated modifiers and base values are preserved.

After a blast, independent Motion is cleared for every nonplayer passenger, matching vanilla's riding-tick reset and preventing synthetic velocity on a same-tick dismount. Passenger motion clipped by an NBT protection write is not added to the root's vector. The mount hierarchy stays intact. Real network-player rider behavior still needs live-client validation.

## Accumulation and range

Each target has a same-tick accumulator. Calls made before that target's next flush add together and cause one combined application. Calls after a flush wait for the next scheduled flush. The library defines exactly three objectives: `PlayerMotion.X`, `PlayerMotion.Y`, and `PlayerMotion.Z`. They are internal accumulators, not another public API.

Each transformed component is clamped to **±1024**, rounded into a score at **0.000001** blocks per tick per unit, and added to its target's score. Each addition saturates the total at ±1,024,000,000 score units. Saturation is per component and per addition, so call order matters when a total reaches a limit. A zero total is cleaned up without an explosion.

Six-decimal fixed-point accumulation is a storage resolution, not a guarantee of six-decimal physical accuracy. Transformations and explosion geometry use **float precision**; precision becomes coarser at large values, and Minecraft's explosion/position/physics calculations add their own error. Many high-magnitude requests also require many crystals and can be expensive. Prefer modest instantaneous impulses; server/client timing and normal physics can make continuous per-tick forces inconsistent.

## Application and limitations

At flush, the target is temporarily moved to **relative Y+10000** in its own dimension. The crystals are created and destroyed there, and the target is teleported back to its original coordinates within the same function. The helper `neac:` dimension contains one fixed UUID marker used to capture rotation; it is not the explosion location. Players temporarily enter creative mode during application and then regain their captured survival/creative/adventure mode.

Nonplayer targets temporarily receive `Invulnerable:1b` to survive the explosions. Enabling it reloads entity NBT and can clip existing Motion components outside ±10; the library compensates for that lost velocity in the additive impulse. Originally invulnerable targets remain invulnerable. For a target newly protected by the library, restoration is immediate only when every resulting Motion component is within **±10**. Otherwise restoration waits until that condition becomes true. **High impulses can leave a target invulnerable for several seconds**, and continuously high motion or an unloaded target can extend that period.

The scheduled flush uses global player anchors and services loaded targets in **dimensions containing players**. Pending impulses and deferred invulnerability restoration in an empty dimension wait until a player enters; loading its chunks alone is insufficient. Multiple players in one dimension do not duplicate a queued launch.

The crystal geometry retains the library's historical eye-height classes (0.4, 1.27, and 1.62). Arbitrarily scaled or unusually sized entities can receive less accurate vectors. This pack does not promise exact physical motion for every entity type or pose. A real network-player session is required to validate client motion, player flight/swim/elytra transitions, and player gamemode restoration in your environment.

## Development checks

```sh
python -B -m unittest tests.test_datapack -v
git diff --check
```

The static suite checks the API, arithmetic, lifecycle, and documentation contracts. Runtime validation must use an isolated official 26.3 world; static tests do not prove client physics or all player states.

Credit to [BigPapi13](https://github.com/BigPapi13/Delta) for the original inspiration, `nedraw` for the end-crystal implementation, and [SuperSwordTW](https://github.com/SuperSwordTW) for math performance and stability improvements.
