# Numbered Function Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `api/` and `internal/` hierarchy with numbered `accumulate/` and `apply/` pipelines modeled after ImpulseMotion, while preserving the public storage/tag API and end-crystal behavior.

**Architecture:** `#player_motion:` enters `accumulate/0`, which advances through numbered resistance, rotation, motion-set, and score stages. Root `schedule_tick` self-schedules with `1t replace` and dispatches the numbered `apply/` pipeline. Ordered helper groups receive local numbers; the unordered state multiplier helpers remain descriptive and unnumbered.

**Tech Stack:** Minecraft Java Edition 26.3 data-pack functions, pack format 121, SNBT storage, `compute default float`, scoreboard fixed-point arithmetic, Python 3 `unittest`, official 26.3 Fabric server.

**Spec:** `docs/superpowers/specs/2026-09-21-numbered-function-layout-design.md`

## Global Constraints

- Preserve the public call sequence: write `storage player_motion: in`, then run `function #player_motion:` as the target.
- Keep exactly `PlayerMotion.X`, `PlayerMotion.Y`, and `PlayerMotion.Z`.
- Preserve six-decimal accumulation, per-call and accumulated `±1024` saturation, same-tick combination, and `player_motion.pending`.
- Preserve relative Y+10000 end-crystal application, vehicle/passenger protection, gamemode restoration, clipped-Motion compensation, and deferred invulnerability restoration.
- Apply resistance in numbered order before `3.looking`; this uniform scaling preserves the intended vector, with only normal float evaluation-order rounding allowed to differ.
- Keep `data/neac/**` byte-identical to ImpulseMotion `master@4308dd963302d2d395c4c85ddfa2ae40a9d627b6`.
- Keep default `minecraft:` prefixes omitted under `data/player_motion`.
- Add no compatibility wrappers for `player_motion:api/**` or `player_motion:internal/**`.
- Keep the self-scheduled loop. Do not create a `minecraft:tick` tag.

## Final Function Tree

```text
load.mcfunction
schedule_tick.mcfunction
accumulate/0.mcfunction
accumulate/1.call.mcfunction
accumulate/2.explosion.mcfunction
accumulate/2.knockback.mcfunction
accumulate/3.looking.mcfunction
accumulate/4.motion_set.mcfunction
accumulate/5.score.mcfunction
accumulate/multiplier/elytra.mcfunction
accumulate/multiplier/in_water.mcfunction
accumulate/multiplier/swim.mcfunction
accumulate/rotation/0.get.mcfunction
accumulate/rotation/1.execution.mcfunction
accumulate/rotation/2.target.mcfunction
apply/0.flush.mcfunction
apply/1.launch.mcfunction
apply/2.protect.mcfunction
apply/3.prepare.mcfunction
apply/4.apply.mcfunction
apply/5.restore_invulnerable.mcfunction
apply/6.cleanup.mcfunction
apply/gamemode/0.get.mcfunction
apply/gamemode/1.restore.mcfunction
apply/passenger/0.prepare_tree.mcfunction
apply/passenger/1.resistance.mcfunction
apply/passenger/2.prepare_boost.mcfunction
apply/passenger/3.boost.mcfunction
apply/passenger/4.protect_tree.mcfunction
apply/passenger/5.protect_nonplayer.mcfunction
apply/passenger/6.restore_tree.mcfunction
apply/summon/0.main.mcfunction
apply/summon/1.crystal.mcfunction
apply/summon/2.loop.mcfunction
```

---

### Task 1: Number the Public Accumulation Pipeline

**Files:**
- Create/move: `player_motion/data/player_motion/function/accumulate/**`
- Delete: `player_motion/data/player_motion/function/api/**`
- Delete: `player_motion/data/player_motion/function/internal/rotation/**`
- Modify: `player_motion/data/player_motion/tags/function/.json`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: `storage player_motion: in`, the target entity context, and the fixed marker UUID `1604-1604-1604-1604-1604`.
- Produces: saturated `PlayerMotion.X/Y/Z` target scores, `player_motion.pending`, and public entry `player_motion:accumulate/0`.

- [ ] **Step 1: Add the failing accumulation-layout contract**

Add this literal test to `DataPackContractTests`:

```python
def test_numbered_accumulation_tree(self):
    function_root = PACK / "data/player_motion/function"
    expected = {
        "0.mcfunction",
        "1.call.mcfunction",
        "2.explosion.mcfunction",
        "2.knockback.mcfunction",
        "3.looking.mcfunction",
        "4.motion_set.mcfunction",
        "5.score.mcfunction",
        "multiplier/elytra.mcfunction",
        "multiplier/in_water.mcfunction",
        "multiplier/swim.mcfunction",
        "rotation/0.get.mcfunction",
        "rotation/1.execution.mcfunction",
        "rotation/2.target.mcfunction",
    }
    accumulate_root = function_root / "accumulate"
    actual = {
        path.relative_to(accumulate_root).as_posix()
        for path in accumulate_root.rglob("*.mcfunction")
    } if accumulate_root.exists() else set()
    self.assertEqual(actual, expected)
    self.assertFalse((function_root / "api").exists())
    self.assertFalse((function_root / "internal/rotation").exists())
```

Change the existing public-tag expectation to:

```python
self.assertEqual(tag, {"values": ["player_motion:accumulate/0"]})
```

- [ ] **Step 2: Change accumulation tests to the new paths before moving code**

Update every accumulation-related `read(...)`, `read_mcfunction_tree(...)`, and literal function call according to this map:

```text
api/call                                       -> accumulate/0
api/process                                    -> accumulate/1.call
api/resistance/explosion                       -> accumulate/2.explosion
api/resistance/knockback                       -> accumulate/2.knockback
api/transform/execution_to_global              -> accumulate/3.looking
api/transform/global_to_target                 -> accumulate/4.motion_set
api/transform/target_to_global                 -> accumulate/4.motion_set
api/accumulate                                 -> accumulate/5.score
api/multiplier/{name}                          -> accumulate/multiplier/{name}
internal/rotation/get                          -> accumulate/rotation/0.get
internal/rotation/capture_execution            -> accumulate/rotation/1.execution
internal/rotation/capture_target               -> accumulate/rotation/2.target
```

When a test previously joined all files below `api/`, join files below `accumulate/`. When transform tests previously joined three files, read `3.looking` and `4.motion_set`; do not duplicate `4.motion_set` in the joined string. Keep all numeric, selector, storage, and saturation assertions unchanged.

- [ ] **Step 3: Run focused tests and verify RED**

```powershell
& 'C:\Users\nea\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest `
  tests.test_datapack.DataPackContractTests.test_numbered_accumulation_tree `
  tests.test_datapack.DataPackContractTests.test_public_tag_points_to_call `
  tests.test_datapack.DataPackContractTests.test_api_defaults_and_fields `
  tests.test_datapack.DataPackContractTests.test_rotation_and_float_transforms `
  tests.test_datapack.DataPackContractTests.test_current_call_multipliers `
  tests.test_datapack.DataPackContractTests.test_fixed_point_saturation -v
```

Expected: FAIL/ERROR because `accumulate/` does not exist and the public tag still points to `api/call`.

- [ ] **Step 4: Move all one-to-one accumulation files**

Create `accumulate/multiplier` and `accumulate/rotation`, then use `git mv` for:

```text
api/call.mcfunction                            -> accumulate/0.mcfunction
api/process.mcfunction                         -> accumulate/1.call.mcfunction
api/resistance/explosion.mcfunction            -> accumulate/2.explosion.mcfunction
api/resistance/knockback.mcfunction            -> accumulate/2.knockback.mcfunction
api/transform/execution_to_global.mcfunction   -> accumulate/3.looking.mcfunction
api/accumulate.mcfunction                      -> accumulate/5.score.mcfunction
api/multiplier/elytra.mcfunction               -> accumulate/multiplier/elytra.mcfunction
api/multiplier/in_water.mcfunction             -> accumulate/multiplier/in_water.mcfunction
api/multiplier/swim.mcfunction                 -> accumulate/multiplier/swim.mcfunction
internal/rotation/get.mcfunction               -> accumulate/rotation/0.get.mcfunction
internal/rotation/capture_execution.mcfunction -> accumulate/rotation/1.execution.mcfunction
internal/rotation/capture_target.mcfunction    -> accumulate/rotation/2.target.mcfunction
```

- [ ] **Step 5: Assemble `4.motion_set` without changing transform formulas**

Move `api/transform/global_to_target.mcfunction` to `accumulate/4.motion_set.mcfunction`. Keep its existing float expressions byte-for-byte. Prepend:

```mcfunction
# Capture target rotation, transform to target-local coordinates, apply state
# multipliers, and transform the result back to global coordinates.
function player_motion:accumulate/rotation/2.target
```

After the existing global-to-target expressions, add:

```mcfunction
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_in_water:true}}} run function player_motion:accumulate/multiplier/in_water
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_fall_flying:true}}} run function player_motion:accumulate/multiplier/elytra
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_swimming:true}}} run function player_motion:accumulate/multiplier/swim
```

Append the complete contents of old `api/transform/target_to_global.mcfunction` after those calls, preserving its four angle providers and the `tmp`, `_.calc.x`, `_.calc.y`, and `_.calc.z` expressions. Delete the old target-to-global file after its contents are present exactly once in `4.motion_set`.

- [ ] **Step 6: Rewrite numbered accumulation orchestration**

In `accumulate/0.mcfunction`, preserve input normalization and the missing-`neac` guard, then end with:

```mcfunction
function player_motion:accumulate/rotation/1.execution
return run function player_motion:accumulate/1.call
```

In `accumulate/1.call.mcfunction`, keep the three current eligibility/vehicle checks. Change vehicle recursion to `player_motion:accumulate/1.call`. Replace the processing tail with:

```mcfunction
execute if data storage player_motion: _.in{is_explosion:true} run function player_motion:accumulate/2.explosion
execute if data storage player_motion: _.in{is_knockback:true} run function player_motion:accumulate/2.knockback

execute if data storage player_motion: _.in{is_looking:true} run function player_motion:accumulate/3.looking
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.x set from storage player_motion: _.in.x
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.y set from storage player_motion: _.in.y
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.z set from storage player_motion: _.in.z

function player_motion:accumulate/4.motion_set
function player_motion:accumulate/5.score
```

Update rotation helper calls to `accumulate/rotation/0.get`. Update the public tag file to exactly:

```json
{"values":["player_motion:accumulate/0"]}
```

Remove empty `api/` and `internal/rotation/` directories.

- [ ] **Step 7: Run focused and full tests to verify GREEN**

Run the command from Step 3, then:

```powershell
& 'C:\Users\nea\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest tests.test_datapack -v
```

Expected: every selected test and the full suite pass. Existing application tests continue to use the still-present `internal/launch` paths in this intermediate commit.

- [ ] **Step 8: Commit the green accumulation migration**

```powershell
git add -A -- player_motion/data/player_motion/function player_motion/data/player_motion/tags/function tests/test_datapack.py
git commit -m "refactor: number accumulation pipeline"
```

---

### Task 2: Number the Scheduled Application Pipeline

**Files:**
- Create/move: `player_motion/data/player_motion/function/load.mcfunction`
- Create/move: `player_motion/data/player_motion/function/schedule_tick.mcfunction`
- Create/move: `player_motion/data/player_motion/function/apply/**`
- Delete: remaining `player_motion/data/player_motion/function/internal/**`
- Modify: `player_motion/data/minecraft/tags/function/load.json`
- Modify: `tests/test_datapack.py`

**Interfaces:**
- Consumes: loaded-player dimension anchors, `player_motion.pending`, and accumulated X/Y/Z scores.
- Produces: one end-crystal application per pending target, unconditional queue cleanup, and recurring deferred invulnerability restoration.

- [ ] **Step 1: Add failing final-tree, root-entry, and reference tests**

Add an `EXPECTED_FUNCTIONS` set containing the exact 34 paths from “Final Function Tree”. Add:

```python
def test_numbered_function_tree(self):
    function_root = PACK / "data/player_motion/function"
    actual = {
        path.relative_to(function_root).as_posix()
        for path in function_root.rglob("*.mcfunction")
    }
    self.assertEqual(actual, EXPECTED_FUNCTIONS)
    self.assertFalse((function_root / "api").exists())
    self.assertFalse((function_root / "internal").exists())

def test_numbered_root_entries(self):
    load_tag = json.loads(
        read("player_motion/data/minecraft/tags/function/load.json")
    )
    self.assertEqual(load_tag, {"values": ["neac:load", "player_motion:load"]})
    self.assertFalse(
        (PACK / "data/minecraft/tags/function/tick.json").exists()
    )

    load = read("player_motion/data/player_motion/function/load.mcfunction")
    tick = read(
        "player_motion/data/player_motion/function/schedule_tick.mcfunction"
    )
    schedule = "schedule function player_motion:schedule_tick 1t replace"
    self.assertIn(schedule, load)
    self.assertEqual(tick.count(schedule), 1)
    self.assertIn("function player_motion:apply/0.flush", tick)

def test_all_player_motion_function_references_resolve(self):
    function_root = PACK / "data/player_motion/function"
    references = re.findall(
        r"\bfunction player_motion:([a-z0-9_./-]+)",
        all_mcfunctions(),
    )
    self.assertTrue(references)
    missing = sorted(
        reference
        for reference in set(references)
        if not (function_root / f"{reference}.mcfunction").is_file()
    )
    self.assertEqual(missing, [])
```

- [ ] **Step 2: Change application test paths before moving code**

Update every application-related test path and literal call using this exact map:

```text
internal/technical/load                       -> load
internal/technical/tick                       -> schedule_tick
internal/technical/flush_dimension            -> apply/0.flush
internal/launch/main                          -> apply/1.launch
internal/launch/protect                       -> apply/2.protect
internal/launch/prepare                       -> apply/3.prepare
internal/launch/apply                         -> apply/4.apply
internal/launch/restore_invulnerable          -> apply/5.restore_invulnerable
internal/launch/cleanup                       -> apply/6.cleanup
internal/launch/gamemode/get                  -> apply/gamemode/0.get
internal/launch/gamemode/restore              -> apply/gamemode/1.restore
internal/launch/passenger/prepare_tree        -> apply/passenger/0.prepare_tree
internal/launch/passenger/resistance          -> apply/passenger/1.resistance
internal/launch/passenger/prepare_boost       -> apply/passenger/2.prepare_boost
internal/launch/passenger/boost               -> apply/passenger/3.boost
internal/launch/passenger/protect_tree        -> apply/passenger/4.protect_tree
internal/launch/passenger/protect_nonplayer   -> apply/passenger/5.protect_nonplayer
internal/launch/passenger/restore_tree        -> apply/passenger/6.restore_tree
internal/summon/main                          -> apply/summon/0.main
internal/summon/crystal                       -> apply/summon/1.crystal
internal/summon/loop                          -> apply/summon/2.loop
```

Change tick expectations to `schedule function player_motion:schedule_tick 1t replace` and `function player_motion:apply/0.flush`. Keep all ordering, safety, NBT, selector, geometry, and cleanup assertions unchanged.

- [ ] **Step 3: Run application and layout tests to verify RED**

```powershell
& 'C:\Users\nea\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest `
  tests.test_datapack.DataPackContractTests.test_numbered_function_tree `
  tests.test_datapack.DataPackContractTests.test_numbered_root_entries `
  tests.test_datapack.DataPackContractTests.test_all_player_motion_function_references_resolve `
  tests.test_datapack.DataPackContractTests.test_explosion_location `
  tests.test_datapack.DataPackContractTests.test_nonplayer_protection_and_clipped_motion_compensation `
  tests.test_datapack.DataPackContractTests.test_restore_invulnerable_waits_for_exact_safe_motion `
  tests.test_datapack.DataPackContractTests.test_passenger_tree_protection `
  tests.test_datapack.DataPackContractTests.test_passenger_effective_resistance_preflight `
  tests.test_datapack.DataPackContractTests.test_tick_flush_and_cleanup `
  tests.test_datapack.DataPackContractTests.test_flush_revalidates_current_player_eligibility_before_mutation -v
```

Expected: FAIL/ERROR because `apply/`, `load`, and `schedule_tick` do not exist yet and `internal/` remains.

- [ ] **Step 4: Move root and application files**

Create `apply/gamemode`, `apply/passenger`, and `apply/summon`. Use `git mv` according to the Step 2 map, plus:

```text
internal/technical/load.mcfunction -> load.mcfunction
internal/technical/tick.mcfunction -> schedule_tick.mcfunction
```

Delete `internal/launch/exp_pos.mcfunction`; `rg 'exp_pos' player_motion` must show no caller before deletion.

- [ ] **Step 5: Rewrite root scheduling and registration**

Keep storage reset and all three objective declarations in `load.mcfunction`. Replace its schedule target with:

```mcfunction
schedule function player_motion:schedule_tick 1t replace
```

Make the executable body of `schedule_tick.mcfunction` exactly:

```mcfunction
schedule function player_motion:schedule_tick 1t replace
execute as @a at @s run function player_motion:apply/0.flush
```

Comments may remain but must contain no stale path. Replace the load tag with:

```json
{
  "values": [
    "neac:load",
    "player_motion:load"
  ]
}
```

Do not create `data/minecraft/tags/function/tick.json`.

- [ ] **Step 6: Rewrite all moved application references**

Apply the Step 2 map to every direct, recursive, scheduled, and macro function call. The resulting top-level calls must include:

```mcfunction
# apply/0.flush
execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/1.launch
execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/6.cleanup
execute as @e[type=!player,tag=player_motion.restore_invulnerable,distance=0..] run function player_motion:apply/5.restore_invulnerable
```

```mcfunction
# apply/1.launch
execute on passengers run function player_motion:apply/passenger/0.prepare_tree
execute on passengers run function player_motion:apply/passenger/4.protect_tree
execute unless entity @s[type=player] run function player_motion:apply/2.protect
function player_motion:apply/3.prepare
execute if score #magnitude PlayerMotion.X matches 1 run function player_motion:apply/4.apply
execute on passengers run function player_motion:apply/passenger/6.restore_tree
execute if entity @s[type=!player,tag=player_motion.restore_invulnerable] run function player_motion:apply/5.restore_invulnerable
```

Update passenger self-recursion to the new numbered file itself. Update `apply/4.apply` to call `apply/gamemode/0.get`, `apply/summon/0.main`, and `apply/gamemode/1.restore`. Update summon recursion to `apply/summon/2.loop`. Do not alter non-path commands.

Remove the empty `internal/` directory after all references migrate.

- [ ] **Step 7: Run focused and full tests to verify GREEN**

Run the command from Step 3, then:

```powershell
& 'C:\Users\nea\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest tests.test_datapack -v
```

Expected: all focused tests and the full suite pass. The exact tree contains 34 files, no `api/` or `internal/` directory exists, and every Player Motion function reference resolves.

- [ ] **Step 8: Commit the green application migration**

```powershell
git add -A -- player_motion tests/test_datapack.py
git commit -m "refactor: number scheduled application pipeline"
```

---

### Task 3: Full Regression and Minecraft 26.3 Runtime Verification

**Files:**
- Modify only if verification exposes a defect: `player_motion/**`, `tests/test_datapack.py`
- Verify: `README.md`
- Verify: `docs/superpowers/specs/2026-09-21-numbered-function-layout-design.md`

**Interfaces:**
- Consumes: completed numbered pipelines from Tasks 1 and 2.
- Produces: a clean, loadable pack with unchanged user-facing API and no stale paths.

- [ ] **Step 1: Run the full static suite and count tests**

```powershell
& 'C:\Users\nea\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B -m unittest tests.test_datapack -v
rg -c '^    def test_' tests/test_datapack.py
```

Expected: unittest reports `OK`; the reported test total equals the `rg` count.

- [ ] **Step 2: Scan for stale paths, forbidden prefixes, and whitespace defects**

```powershell
rg -n 'player_motion:(api|internal)/|function\\(api|internal)\\|function/(api|internal)/' player_motion tests README.md
rg -n 'minecraft:' player_motion/data/player_motion
git diff --check
```

Expected: both `rg` commands exit 1 with no matches. `git diff --check` exits 0. Historical specs/plans are intentionally excluded from the stale-path scan.

- [ ] **Step 3: Verify `neac` remains byte-identical to ImpulseMotion**

```powershell
$reference = Join-Path $env:TEMP 'impulse-motion-reference\ImpulseMotion\data\neac'
$local = Resolve-Path 'player_motion\data\neac'
git diff --no-index -- $reference $local
```

Expected: exit 0 and no diff output.

- [ ] **Step 4: Verify load and reload on the local 26.3 server**

From `D:\Minecraft\Git\datapacks\PlayerMotion`, start:

```powershell
java -Xms1G -Xmx9G -jar fabric-server-launch.jar nogui
```

After the console reports `Done`, enter:

```text
reload
datapack list enabled
stop
```

Expected: reload completes without `Failed to load function`, `Couldn't load tag`, unknown-function, or command-parse errors; the enabled list includes the local `player_motion` pack; shutdown completes normally.

- [ ] **Step 5: Review the final history and commit only actual corrections**

```powershell
git status --short
git diff --check HEAD~2..HEAD
git log -4 --oneline
```

If runtime or regression verification required corrections, stage only the corrected pack/test files and commit:

```powershell
git add -- player_motion tests/test_datapack.py
git commit -m "fix: complete numbered function migration"
```

If no correction was required, do not create an empty commit.
