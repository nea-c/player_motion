# Player Motion 26.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a Minecraft Java Edition 26.3 Player Motion data pack with an ImpulseMotion-compatible storage API, six-decimal fixed-point tick accumulation, and the existing end-crystal motion mechanism.

**Architecture:** Each API call normalizes `storage player_motion: in`, resolves the requested coordinate system and target-state modifiers with 26.3 float compute expressions, and adds a saturated global vector to three entity scores. A scheduled tick flush converts those scores into the existing repeated/full plus residual end-crystal explosions at the target's relative Y+10000 position; the `neac:` dimension and its single fixed-UUID marker are used only for rotation capture.

**Tech Stack:** Minecraft Java Edition 26.3 data-pack functions and macros, pack format 121.0, `compute default float`, SNBT storage, scoreboard fixed-point arithmetic, Python 3 standard-library static tests, official 26.3 dedicated server for runtime verification.

**Spec:** `docs/superpowers/specs/2026-09-19-player-motion-26-3-design.md`

## Global Constraints

- The only public entry point is `function #player_motion:` with input in `storage player_motion: in`.
- Support `x`, `y`, `z`, `is_looking`, `is_vehicle_execution`, `is_knockback`, `is_explosion`, and `multiplier.{elytra,swim,in_water}`.
- Defaults are `x/y/z:0.0`, all booleans false, `elytra:0.5`, `swim:0.5`, and `in_water:1.5`.
- Use exactly three objectives: `PlayerMotion.X`, `PlayerMotion.Y`, and `PlayerMotion.Z`.
- One score unit equals `0.000001` Motion; per-call and accumulated components saturate at `±1,024,000,000`.
- Multipliers and resistance flags affect only the current call, never previously accumulated scores.
- Use the empty `neac:` dimension and UUID `[I;5636,369366532,369360896,5636]` only for rotation capture.
- Summon end crystals in the target's current dimension at the original execution position plus relative Y+10000.
- Remove the old scoreboard API and provide no compatibility shim.
- Do not add enchantment-based motion assets.

---

## File Structure

The implementation will use these boundaries:

- `tests/test_datapack.py`: static contract, layout, numeric-limit, and obsolete-interface checks.
- `player_motion/data/player_motion/tags/function/.json`: sole public function tag.
- `player_motion/data/player_motion/function/api/call.mcfunction`: default merge, eligibility, vehicle routing, and pipeline orchestration.
- `player_motion/data/player_motion/function/api/resistance/*.mcfunction`: the two optional resistance factors.
- `player_motion/data/player_motion/function/api/transform/*.mcfunction`: execution-local/global and target-local/global transforms.
- `player_motion/data/player_motion/function/api/multiplier/*.mcfunction`: water, elytra, and swimming adjustments to only the current call.
- `player_motion/data/player_motion/function/api/accumulate.mcfunction`: float-to-fixed conversion, per-call saturation, accumulated saturation, and pending tag.
- `player_motion/data/player_motion/function/internal/rotation/*.mcfunction`: marker-based execution and target rotation capture.
- `player_motion/data/player_motion/function/internal/technical/load.mcfunction`: three objectives, storage initialization, marker initialization, and tick scheduling.
- `player_motion/data/player_motion/function/internal/technical/tick.mcfunction`: one flush per pending entity.
- `player_motion/data/player_motion/function/internal/launch/*.mcfunction`: score extraction, explosion geometry, temporary state, relative teleport, restoration, and cleanup.
- `player_motion/data/player_motion/function/internal/summon/*.mcfunction`: full and residual crystal spawning.
- `player_motion/data/neac/**`: void dimension and one fixed marker.
- `README.md`: new API documentation and limitations.

### Task 1: Add the static contract test and 26.3 pack skeleton

**Files:**
- Create: `tests/test_datapack.py`
- Modify: `player_motion/pack.mcmeta`
- Create: `player_motion/data/player_motion/tags/function/.json`
- Create: `player_motion/data/neac/dimension/.json`
- Create: `player_motion/data/neac/dimension_type/void.json`
- Create: `player_motion/data/neac/function/load.mcfunction`
- Modify: `player_motion/data/minecraft/tags/function/load.json`
- Modify: `player_motion/data/player_motion/function/internal/technical/load.mcfunction`

**Interfaces:**
- Produces: pack format 121.0, public tag `#player_motion:`, objectives `PlayerMotion.X/Y/Z`, dimension `neac:`, and marker UUID `[I;5636,369366532,369360896,5636]`.
- Consumes: none.

- [ ] **Step 1: Write the failing skeleton tests**

Create `tests/test_datapack.py` with `unittest`, a `ROOT` pointing to the repository root, helpers `read(path)` and `all_mcfunctions()`, and these assertions:

```python
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "player_motion"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def all_mcfunctions() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(PACK.rglob("*.mcfunction"))
    )


class DataPackContractTests(unittest.TestCase):
    def test_pack_targets_26_3(self):
        metadata = json.loads(read("player_motion/pack.mcmeta"))
        self.assertEqual(metadata["pack"]["pack_format"], 121)

    def test_public_tag_points_to_call(self):
        tag = json.loads(read("player_motion/data/player_motion/tags/function/.json"))
        self.assertEqual(tag, {"values": ["player_motion:api/call"]})

    def test_exactly_three_objectives_are_created(self):
        commands = all_mcfunctions()
        objectives = re.findall(r"^scoreboard objectives add (\S+)", commands, re.MULTILINE)
        self.assertEqual(objectives, ["PlayerMotion.X", "PlayerMotion.Y", "PlayerMotion.Z"])

    def test_neac_marker_contract(self):
        load = read("player_motion/data/neac/function/load.mcfunction")
        self.assertIn("in neac:", load)
        self.assertIn("[I;5636,369366532,369360896,5636]", load)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the skeleton tests and verify failure**

Run: `python -m unittest tests.test_datapack -v`

Expected: failures for pack format, missing public tag, old objective count, and missing `neac:` resources.

- [ ] **Step 3: Implement the 26.3 skeleton**

Set `pack_format` to `121`. Add the public tag with exactly `{"values":["player_motion:api/call"]}`. Copy the reviewed ImpulseMotion void dimension definition into `data/neac`, and make `neac:load`:

1. probe `in neac:` and store success in `storage neac: DimensionGenerated`;
2. report a clear error if the dimension is unavailable;
3. forceload `-1 -1 1 1` in `neac:`;
4. summon the fixed marker only unless that UUID already exists.

Rewrite the Player Motion load function so its only objective declarations are:

```mcfunction
scoreboard objectives add PlayerMotion.X dummy
scoreboard objectives add PlayerMotion.Y dummy
scoreboard objectives add PlayerMotion.Z dummy
```

Initialize `storage player_motion: _`, invoke `neac:load` through the Minecraft load tag, and schedule `player_motion:internal/technical/tick` using `1t replace` so `/reload` cannot duplicate the loop.

- [ ] **Step 4: Run the skeleton tests**

Run: `python -m unittest tests.test_datapack -v`

Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit the skeleton**

```bash
git add tests/test_datapack.py player_motion/pack.mcmeta player_motion/data/minecraft/tags/function/load.json player_motion/data/player_motion/tags/function/.json player_motion/data/player_motion/function/internal/technical/load.mcfunction player_motion/data/neac
git commit -m "feat: add 26.3 pack and public API skeleton"
```

### Task 2: Implement input normalization, routing, and coordinate transforms

**Files:**
- Create: `player_motion/data/player_motion/function/api/call.mcfunction`
- Create: `player_motion/data/player_motion/function/api/process.mcfunction`
- Create: `player_motion/data/player_motion/function/api/resistance/knockback.mcfunction`
- Create: `player_motion/data/player_motion/function/api/resistance/explosion.mcfunction`
- Create: `player_motion/data/player_motion/function/api/transform/execution_to_global.mcfunction`
- Create: `player_motion/data/player_motion/function/api/transform/global_to_target.mcfunction`
- Create: `player_motion/data/player_motion/function/api/transform/target_to_global.mcfunction`
- Create: `player_motion/data/player_motion/function/internal/rotation/capture_execution.mcfunction`
- Create: `player_motion/data/player_motion/function/internal/rotation/capture_target.mcfunction`
- Create: `player_motion/data/player_motion/function/internal/rotation/get.mcfunction`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: marker UUID and storage initialized by Task 1.
- Produces: `storage player_motion: _.calc.{x,y,z}` containing the current call's adjusted global vector, before state multipliers and score accumulation.

- [ ] **Step 1: Add failing API field and transform tests**

Add tests that read `api/call.mcfunction` and the transform directory and assert the exact defaults `elytra:0.5`, `swim:0.5`, `in_water:1.5`, all seven scalar/boolean input keys, `on vehicle`, both resistance attribute names, `compute default float`, `sin`, and `cos`. Assert `capture_execution.mcfunction` executes as UUID `1604-1604-1604-1604-1604` in `neac:`.

- [ ] **Step 2: Run the API tests and verify failure**

Run: `python -m unittest tests.test_datapack.DataPackContractTests.test_api_defaults_and_fields tests.test_datapack.DataPackContractTests.test_rotation_and_float_transforms -v`

Expected: both tests fail because the API pipeline does not exist.

- [ ] **Step 3: Implement default merge and eligibility routing**

In `api/call.mcfunction`, reset only private working storage, merge `storage player_motion: in` over this exact compound, and preserve the invocation rotation before changing executor:

```snbt
{x:0.0,y:0.0,z:0.0,is_looking:false,is_vehicle_execution:false,is_knockback:false,is_explosion:false,multiplier:{elytra:0.5,swim:0.5,in_water:1.5}}
```

Reject spectator players and creative flying players that are not fall-flying. When mounted, return failure if `is_vehicle_execution` is false; otherwise recurse with `execute on vehicle run function player_motion:api/process` until there is no higher vehicle. Do not overwrite the originally captured command execution rotation during recursion.

- [ ] **Step 4: Implement float transforms and resistance functions**

Use the ImpulseMotion rotation matrices with degrees converted by `0.017453292519943295`:

```text
tmp = y*sin(pitch) + z*cos(pitch)
global.x = x*cos(yaw) - tmp*sin(yaw)
global.y = y*cos(pitch) - z*sin(pitch)
global.z = x*sin(yaw) + tmp*cos(yaw)
```

Apply this only for `is_looking:true`; otherwise copy input directly to the global calculation fields. Implement the inverse target transform and its forward inverse as separate functions so Task 3 can modify the target-local positive forward component.

Read each requested resistance with `attribute @s <attribute> get 1000000`, store at scale `0.000001`, calculate `max(1-resistance,0)`, and multiply only `_.calc.x/y/z`. If both flags are true, call both functions sequentially.

- [ ] **Step 5: Run all static tests**

Run: `python -m unittest tests.test_datapack -v`

Expected: all Task 1 and Task 2 tests pass.

- [ ] **Step 6: Commit input processing**

```bash
git add tests/test_datapack.py player_motion/data/player_motion/function/api player_motion/data/player_motion/function/internal/rotation
git commit -m "feat: add storage input and float transforms"
```

### Task 3: Add per-call multipliers and overflow-safe accumulation

**Files:**
- Create: `player_motion/data/player_motion/function/api/multiplier/elytra.mcfunction`
- Create: `player_motion/data/player_motion/function/api/multiplier/in_water.mcfunction`
- Create: `player_motion/data/player_motion/function/api/multiplier/swim.mcfunction`
- Create: `player_motion/data/player_motion/function/api/accumulate.mcfunction`
- Modify: `player_motion/data/player_motion/function/api/process.mcfunction`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: current-call global vector `_.calc.{x,y,z}` and target rotation from Task 2.
- Produces: saturated target scores in `PlayerMotion.X/Y/Z` and tag `player_motion.pending`.

- [ ] **Step 1: Add failing multiplier and saturation tests**

Add assertions that:

- water reads `_.in.multiplier.in_water` and updates all three current-call local fields;
- elytra and swim each update only local positive Z;
- `accumulate.mcfunction` contains `1000000`, `1024000000`, and `-1024000000`;
- it adds fake-player delta scores into `@s PlayerMotion.X/Y/Z` before applying accumulated clamps;
- only the tag `player_motion.pending` marks queued entities.

- [ ] **Step 2: Run the new tests and verify failure**

Run: `python -m unittest tests.test_datapack.DataPackContractTests.test_current_call_multipliers tests.test_datapack.DataPackContractTests.test_fixed_point_saturation -v`

Expected: both tests fail because multiplier and accumulator functions are absent.

- [ ] **Step 3: Implement target-state multipliers**

Convert the current global vector to target-local coordinates. In water, multiply local X/Y/Z by `multiplier.in_water`. While fall-flying, multiply local Z by `multiplier.elytra` only when local Z is greater than zero. While swimming, multiply local Z by `multiplier.swim` only when local Z is greater than zero. Convert the modified current-call vector back to global coordinates; never load target accumulated scores into these functions.

- [ ] **Step 4: Implement fixed-point accumulation**

For each component, use a compute expression equivalent to:

```text
round(clamp(current_component, -1024.0, 1024.0) * 1000000)
```

Store the three results in fake players such as `#delta` under their corresponding X/Y/Z objectives. Add each delta to the target score. Because both operands were already clamped, the temporary signed sum cannot exceed `±2,048,000,000`; immediately set results matching `1024000001..` to `1024000000` and results matching `..-1024000001` to `-1024000000`. Add `player_motion.pending` only after all three scores are valid.

- [ ] **Step 5: Run all static tests**

Run: `python -m unittest tests.test_datapack -v`

Expected: all tests pass.

- [ ] **Step 6: Commit accumulation**

```bash
git add tests/test_datapack.py player_motion/data/player_motion/function/api
git commit -m "feat: accumulate motion with six-decimal scores"
```

### Task 4: Port end-crystal geometry to float compute and three objectives

**Files:**
- Rewrite: `player_motion/data/player_motion/function/internal/launch/main.mcfunction`
- Create: `player_motion/data/player_motion/function/internal/launch/prepare.mcfunction`
- Create: `player_motion/data/player_motion/function/internal/launch/apply.mcfunction`
- Rewrite: `player_motion/data/player_motion/function/internal/launch/gamemode/get.mcfunction`
- Rewrite: `player_motion/data/player_motion/function/internal/launch/gamemode/restore.mcfunction`
- Rewrite: `player_motion/data/player_motion/function/internal/summon/main.mcfunction`
- Rewrite: `player_motion/data/player_motion/function/internal/summon/crystal.mcfunction`
- Rewrite: `player_motion/data/player_motion/function/internal/summon/loop.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/eyelevel.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/full_power/sine.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/full_power/tp.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/full_power/trig.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/looking_to_xyz.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/main.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/trig/arcsine.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/math/trig/sine.mcfunction`
- Delete: `player_motion/data/player_motion/function/internal/technical/trig.mcfunction`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: saturated target X/Y/Z scores and target execution context.
- Produces: `storage player_motion: _.launch` containing global vector, magnitude, full-explosion count, residual power, and the `full_d`/`d` macro distances expected by summon functions.

- [ ] **Step 1: Add failing end-crystal geometry tests**

Assert that launch extraction scales scores by `0.000001`, geometry uses `compute default float`, full impulses use `0.8`, explosion falloff uses `12`, and summon functions still create/damage `end_crystal`. Assert no file under `internal/launch` contains `in neac:` and that `apply.mcfunction` contains both `tp ~ ~10000 ~` and `positioned ~ ~10000 ~`.

- [ ] **Step 2: Run the geometry tests and verify failure**

Run: `python -m unittest tests.test_datapack.DataPackContractTests.test_end_crystal_geometry tests.test_datapack.DataPackContractTests.test_explosion_location -v`

Expected: failures because the old 0.0001 scoreboard geometry and extra objectives remain.

- [ ] **Step 3: Implement storage-based geometry**

Extract scores to `_.launch.x/y/z` at scale `0.000001`. Replace lookup tables and integer trigonometry with float compute expressions that preserve the established geometry. Use normalized vertical and horizontal components directly, avoiding an unnecessary inverse-trigonometric round trip:

```text
magnitude = sqrt(x*x + y*y + z*z)
full_count = floor(magnitude / 0.8)
residual = magnitude - full_count*0.8
falloff_distance = (1 - power) * 12
unit_y = y / magnitude
unit_horizontal = sqrt(x*x + z*z) / magnitude
q = clamp(unit_horizontal * eye_height / falloff_distance, -1, 1)
d = -(eye_height*unit_y + falloff_distance*sqrt(1-q*q))
```

Calculate the same expression with `power=0.8` for `full_d`. Guard the zero-vector and zero-residual cases before division. Use a fake player in `PlayerMotion.X` for the integer `full_count`, keeping the objective count at three.

- [ ] **Step 4: Preserve target state and apply explosions at relative Y+10000**

For players, store game mode in a fake player under `PlayerMotion.X`, temporarily switch to creative only during synthetic explosion handling, and restore survival/creative/adventure exactly. Spectators have already been rejected. For living targets that expose `explosion_knockback_resistance`, add the scoped `-1 add_multiplied_total` modifier before explosion and remove it afterward. Skip attribute and game-mode commands for non-player vehicles.

Run the explosion in the target's current dimension and original command context:

```mcfunction
tp @s ~ ~10000 ~
execute rotated as @s positioned ~ ~10000 ~ run function player_motion:internal/summon/main with storage player_motion: _.launch
tp @s ~ ~ ~
```

Do not insert `execute in neac:` around launch or summon. Keep crystals transient by immediately running `damage @s 0` as each crystal is summoned.

- [ ] **Step 5: Delete obsolete lookup-table math and run tests**

Run: `python -m unittest tests.test_datapack -v`

Expected: all tests pass; no old trig files or tables remain.

- [ ] **Step 6: Commit the explosion port**

```bash
git add -A player_motion/data/player_motion/function/internal tests/test_datapack.py
git commit -m "feat: port crystal motion to float geometry"
```

### Task 5: Wire the tick flush and remove the old API

**Files:**
- Rewrite: `player_motion/data/player_motion/function/internal/technical/tick.mcfunction`
- Delete: `player_motion/data/player_motion/function/api/launch_xyz.mcfunction`
- Delete: `player_motion/data/player_motion/function/api/launch_looking.mcfunction`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: `player_motion.pending` and accumulated scores from Task 3, launch pipeline from Task 4.
- Produces: one flush per pending target, followed by cleared scores and tag.

- [ ] **Step 1: Add failing queue and cleanup tests**

Assert that tick reschedules itself with `1t replace`, executes `as @e[tag=player_motion.pending] at @s`, and calls launch once. Assert launch cleanup resets all three target scores and removes `player_motion.pending`. Assert old launch functions do not exist and `player_motion.api.launch` appears nowhere.

- [ ] **Step 2: Run the queue tests and verify failure**

Run: `python -m unittest tests.test_datapack.DataPackContractTests.test_tick_flush_and_cleanup tests.test_datapack.DataPackContractTests.test_old_api_removed -v`

Expected: failures because the old global flag/tag flow and files still exist.

- [ ] **Step 3: Implement the pending-entity tick flush**

Use:

```mcfunction
schedule function player_motion:internal/technical/tick 1t replace
execute as @e[tag=player_motion.pending] at @s run function player_motion:internal/launch/main
```

Have `launch/main` return without explosions for an all-zero vector, but always reset `@s PlayerMotion.X/Y/Z` and remove the pending tag through a cleanup function. Ensure every nonzero target is processed independently and scratch fake-player values cannot leak between targets.

- [ ] **Step 4: Remove the old public API and run tests**

Delete both old functions and remove all references to the old objective, `$function_called`, and `player_motion.launch`.

Run: `python -m unittest tests.test_datapack -v`

Expected: all tests pass.

- [ ] **Step 5: Commit tick integration**

```bash
git add -A player_motion tests/test_datapack.py
git commit -m "feat: flush accumulated motion once per tick"
```

### Task 6: Document and validate the finished pack

**Files:**
- Rewrite: `README.md`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: completed public behavior from Tasks 1–5.
- Produces: user documentation and final verification evidence.

- [ ] **Step 1: Add failing documentation tests**

Assert README contains `storage player_motion: in`, `function #player_motion:`, every input field, the three implementation defaults, `0.000001`, `±1024`, same-tick accumulation, relative Y+10000, and a float-precision caveat. Assert README does not show either old API function.

- [ ] **Step 2: Run the documentation tests and verify failure**

Run: `python -m unittest tests.test_datapack.DataPackContractTests.test_readme_documents_new_api -v`

Expected: failure because README still documents the scoreboard API.

- [ ] **Step 3: Rewrite README**

Document a minimal XYZ example, a looking-relative example, the full input compound, defaults, field semantics, resistance multiplication, state multipliers, vehicle routing, rejected states, tick accumulation, range and fixed-point representation, and the distinction between six-decimal accumulation and physical float precision.

- [ ] **Step 4: Run static validation**

Run:

```bash
python -m unittest tests.test_datapack -v
git diff --check
```

Expected: all tests pass and `git diff --check` emits no errors.

- [ ] **Step 5: Run a 26.3 server load smoke test**

Start an isolated official 26.3 server with this pack in a disposable world, accept the EULA only inside that disposable directory, run `/reload`, and inspect the log.

Expected: the pack is enabled with no JSON, function, macro, command-parser, registry, or unknown-function errors; `neac:` exists and contains exactly the fixed UUID marker.

- [ ] **Step 6: Run focused runtime cases**

Verify in 26.3:

1. `{x:1.0}` moves globally on X.
2. `{z:1.0,is_looking:true}` follows invocation facing.
3. Two `{x:0.000001}` calls before a flush produce score `2` before application.
4. Positive and negative oversized inputs saturate at `±1,024,000,000`.
5. Knockback and explosion resistance flags scale only their own call.
6. Water scales XYZ; elytra and swim scale only positive target-local Z.
7. Vehicle false rejects mounted execution; vehicle true pushes the root vehicle.
8. Spectator and creative flight calls are rejected.
9. The target returns to its original coordinates and no crystals persist.
10. Multiple pending targets in different dimensions each receive their own impulse in that same dimension.

- [ ] **Step 7: Commit documentation and any verified corrections**

```bash
git add README.md tests/test_datapack.py player_motion
git commit -m "docs: document Player Motion 26.3 API"
```

- [ ] **Step 8: Perform final repository review**

Run:

```bash
git status --short
git log --oneline -7
python -m unittest tests.test_datapack -v
```

Expected: clean status, the task commits are present, and every test passes.
