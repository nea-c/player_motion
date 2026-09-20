import json
import math
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "player_motion"

EXPECTED_FUNCTIONS = {
    "load.mcfunction",
    "schedule_tick.mcfunction",
    "accumulate/0.mcfunction",
    "accumulate/1.call.mcfunction",
    "accumulate/2.explosion.mcfunction",
    "accumulate/2.knockback.mcfunction",
    "accumulate/3.looking.mcfunction",
    "accumulate/4.motion_set.mcfunction",
    "accumulate/5.score.mcfunction",
    "accumulate/multiplier/elytra.mcfunction",
    "accumulate/multiplier/in_water.mcfunction",
    "accumulate/multiplier/swim.mcfunction",
    "accumulate/rotation/0.get.mcfunction",
    "accumulate/rotation/1.execution.mcfunction",
    "accumulate/rotation/2.target.mcfunction",
    "apply/0.flush.mcfunction",
    "apply/1.launch.mcfunction",
    "apply/2.protect.mcfunction",
    "apply/3.prepare.mcfunction",
    "apply/4.apply.mcfunction",
    "apply/5.restore_invulnerable.mcfunction",
    "apply/6.cleanup.mcfunction",
    "apply/gamemode/0.get.mcfunction",
    "apply/gamemode/1.restore.mcfunction",
    "apply/passenger/0.prepare_tree.mcfunction",
    "apply/passenger/1.resistance.mcfunction",
    "apply/passenger/2.prepare_boost.mcfunction",
    "apply/passenger/3.boost.mcfunction",
    "apply/passenger/4.protect_tree.mcfunction",
    "apply/passenger/5.protect_nonplayer.mcfunction",
    "apply/passenger/6.restore_tree.mcfunction",
    "apply/summon/0.main.mcfunction",
    "apply/summon/1.crystal.mcfunction",
    "apply/summon/2.loop.mcfunction",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def all_mcfunctions() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(PACK.rglob("*.mcfunction"))
    )


def read_mcfunction_tree(relative: str) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((PACK / relative).rglob("*.mcfunction"))
    )


def launch_geometry(vector, eye_height=1.62):
    """Evaluate the arithmetic emitted by prepare, rounding each provider to float32."""
    def f32(value):
        return struct.unpack("f", struct.pack("f", value))[0]

    values = dict(zip("xyz", map(f32, vector)))
    values["eye_height"] = f32(eye_height)

    def evaluate(provider):
        if isinstance(provider, (int, float)):
            return f32(provider)
        kind = provider["type"]
        if kind == "storage":
            return values[provider["path"].removeprefix("_.launch.")]
        if kind in ("add", "mul", "min", "max"):
            inputs = list(map(evaluate, provider["inputs"]))
            if kind == "add":
                result = inputs[0]
                for value in inputs[1:]:
                    result = f32(result + value)
            elif kind == "mul":
                result = inputs[0]
                for value in inputs[1:]:
                    result = f32(result * value)
            else:
                result = (min if kind == "min" else max)(inputs)
        elif kind in ("div", "sub"):
            left, right = evaluate(provider["left"]), evaluate(provider["right"])
            result = left / right if kind == "div" else left - right
        else:
            functions = {"sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil, "negate": lambda x: -x}
            result = functions[kind](evaluate(provider["input"]))
        return f32(result)

    source = read("player_motion/data/player_motion/function/apply/3.prepare.mcfunction")
    for line in source.splitlines():
        match = re.search(r"_\.launch\.(\w+) set compute default float (.+)$", line)
        if not match:
            continue
        if line.startswith("execute if score # PlayerMotion.Y") and values["residual"] == 0:
            continue
        name, expression = match.groups()
        expression = re.sub(r"([,{])([a-z_]+):", r'\1"\2":', expression)
        values[name] = evaluate(json.loads(expression))
    return values


class DataPackContractTests(unittest.TestCase):
    def test_readme_documents_new_api(self):
        readme = read("README.md")
        for required in (
            "storage player_motion: in", "function #player_motion:",
            "x:", "y:", "z:", "is_looking", "is_vehicle_execution",
            "is_knockback", "is_explosion", "multiplier",
            "elytra:0.5", "swim:0.5", "in_water:1.5",
            "0.000001", "±1024", "same-tick", "Y+10000",
            "float precision", "Invulnerable", "±10",
            "dimensions containing players",
            "passenger tree", "independent Motion",
            "every nonplayer passenger", "skipped before",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)
        self.assertNotRegex(readme, r"player_motion:(?:api|internal)/")
        for obsolete in ("player_motion.api.launch_xyz", "player_motion.api.launch_looking"):
            self.assertNotIn(obsolete, readme)

    def test_pack_targets_26_3(self):
        metadata = json.loads(read("player_motion/pack.mcmeta"))
        self.assertEqual(metadata["pack"]["pack_format"], 121)
        self.assertEqual(metadata["pack"].get("min_format"), 121)
        self.assertEqual(metadata["pack"].get("max_format"), 121)

    def test_neac_dimension_matches_impulse_motion_registry(self):
        dimension = json.loads(read("player_motion/data/neac/dimension/.json"))
        self.assertEqual(
            dimension,
            {
                "type": "neac:void",
                "generator": {
                    "type": "flat",
                    "settings": {
                        "biome": "the_void",
                        "lakes": False,
                        "features": False,
                        "layers": [],
                        "structure_overrides": [],
                    },
                },
            },
        )

        dimension_type = json.loads(read("player_motion/data/neac/dimension_type/void.json"))
        self.assertEqual(
            dimension_type,
            {
                "ambient_light": 0,
                "attributes": {
                    "minecraft:gameplay/bed_rule": {
                        "can_set_spawn": "never",
                        "can_sleep": "never",
                        "destroy_on_use": False,
                        "destroy_on_leave": False,
                    },
                    "minecraft:gameplay/nether_portal_spawns_piglin": False,
                    "minecraft:gameplay/respawn_anchor_works": False,
                    "minecraft:gameplay/piglins_zombify": False,
                    "minecraft:visual/ambient_light_color": "#ffffff",
                    "minecraft:gameplay/can_start_raid": False,
                    "minecraft:gameplay/water_evaporates": False,
                    "minecraft:visual/fog_color": "#c0d8ff",
                    "minecraft:visual/sky_color": "#78a7ff",
                },
                "coordinate_scale": 1,
                "has_ceiling": False,
                "has_skylight": True,
                "has_fixed_time": True,
                "has_ender_dragon_fight": False,
                "height": 64,
                "infiniburn": "#infiniburn_overworld",
                "logical_height": 64,
                "min_y": -32,
                "monster_spawn_block_light_limit": 0,
                "monster_spawn_light_level": 0,
            },
        )

    def test_public_tag_points_to_call(self):
        tag = json.loads(read("player_motion/data/player_motion/tags/function/.json"))
        self.assertEqual(tag, {"values": ["player_motion:accumulate/0"]})

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

    def test_numbered_function_tree(self):
        function_root = PACK / "data/player_motion/function"
        actual = {
            path.relative_to(function_root).as_posix()
            for path in function_root.rglob("*.mcfunction")
        }
        self.assertEqual(actual, EXPECTED_FUNCTIONS)
        self.assertFalse((function_root / "api").exists())
        self.assertFalse((function_root / "internal").exists())
        self.assertNotIn("launch/main", all_mcfunctions())

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

    def test_exactly_three_objectives_are_created(self):
        commands = all_mcfunctions()
        objectives = re.findall(r"^scoreboard objectives add (\S+)", commands, re.MULTILINE)
        self.assertEqual(objectives, ["PlayerMotion.X", "PlayerMotion.Y", "PlayerMotion.Z"])

    def test_scratch_scoreholders_are_reused_and_reset(self):
        commands = all_mcfunctions()
        fake_players = set(
            re.findall(
                r"(?<!\S)(#[A-Za-z0-9_.+-]*)(?=\s+PlayerMotion\.[XYZ]\b)",
                commands,
            )
        )
        self.assertEqual(
            fake_players,
            {"#", "#passenger_failed", "#passenger_launched"},
        )

        accumulate = read(
            "player_motion/data/player_motion/function/accumulate/5.score.mcfunction"
        )
        for objective in "XYZ":
            reset = f"scoreboard players reset # PlayerMotion.{objective}"
            self.assertIn(reset, accumulate)
            self.assertLess(accumulate.index(reset), accumulate.index("tag @s add"))

        flush = read("player_motion/data/player_motion/function/apply/0.flush.mcfunction")
        for fake_player in ("#", "#passenger_failed", "#passenger_launched"):
            self.assertIn(f"scoreboard players reset {fake_player}", flush)

        gamemode = read_mcfunction_tree(
            "data/player_motion/function/apply/gamemode"
        )
        self.assertNotIn("scoreboard players", gamemode)
        self.assertIn("_.launch.mode", gamemode)

    def test_default_minecraft_namespace_is_omitted(self):
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((PACK / "data/player_motion").rglob("*"))
            if path.is_file()
        )
        self.assertNotIn("minecraft:", sources)

    def test_neac_marker_contract(self):
        commands = [
            line.strip()
            for line in read("player_motion/data/neac/function/load.mcfunction").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(
            commands,
            [
                "data modify storage neac: DimensionGenerated set value 0b",
                "execute store success storage neac: DimensionGenerated byte 1 in neac: run help help .",
                'execute unless data storage neac: {DimensionGenerated:1b} run tellraw @a {"text":"==============================\\nディメンションの生成を確認できませんでした。\\n生成にはワールドの再読み込みが必要です。\\n==============================","color":"#ff0000"}',
                "execute if data storage neac: {DimensionGenerated:1b} in neac: run forceload add -1 -1 1 1",
                "execute if data storage neac: {DimensionGenerated:1b} in neac: run summon marker 0.0 0.0 0.0 {UUID:[I;5636,369366532,369360896,5636]}",
            ],
        )

    def test_api_defaults_and_fields(self):
        call_path = PACK / "data/player_motion/function/accumulate/0.mcfunction"
        self.assertTrue(call_path.is_file(), "accumulate/0.mcfunction must exist")
        for relative in (
            "1.call.mcfunction",
            "2.knockback.mcfunction",
            "2.explosion.mcfunction",
        ):
            self.assertTrue(
                (call_path.parent / relative).is_file(), f"accumulate/{relative} must exist"
            )
        call = read("player_motion/data/player_motion/function/accumulate/0.mcfunction")
        api = read_mcfunction_tree("data/player_motion/function/accumulate")

        defaults = (
            "{x:0.0,y:0.0,z:0.0,is_looking:false,"
            "is_vehicle_execution:false,is_knockback:false,is_explosion:false,"
            "multiplier:{elytra:0.5,swim:0.5,in_water:1.5}}"
        )
        self.assertIn(f"{{in:{defaults}}}", call)
        self.assertIn("_.in merge from storage player_motion: in", call)
        self.assertIn("elytra:0.5", call)
        self.assertIn("swim:0.5", call)
        self.assertIn("in_water:1.5", call)
        for key in (
            "x",
            "y",
            "z",
            "is_looking",
            "is_vehicle_execution",
            "is_knockback",
            "is_explosion",
        ):
            self.assertRegex(call, rf"(?:^|[{{,]){key}:")
        self.assertIn("on vehicle", api)
        self.assertIn("knockback_resistance", api)
        self.assertIn("explosion_knockback_resistance", api)
        self.assertIn("get 1000000", api)
        self.assertIn("float 0.000001", api)
        self.assertLess(
            call.index("accumulate/rotation/1.execution"),
            call.index("accumulate/1.call"),
        )

    def test_rotation_and_float_transforms(self):
        capture_path = (
            PACK
            / "data/player_motion/function/accumulate/rotation/1.execution.mcfunction"
        )
        self.assertTrue(capture_path.is_file(), "capture_execution.mcfunction must exist")
        for relative in ("3.looking.mcfunction", "4.motion_set.mcfunction"):
            self.assertTrue(
                (capture_path.parent.parent / relative).is_file(),
                f"accumulate/{relative} must exist",
            )
        for relative in ("2.target.mcfunction", "0.get.mcfunction"):
            self.assertTrue(
                (capture_path.parent / relative).is_file(),
                f"accumulate/rotation/{relative} must exist",
            )
        transforms = "\n".join(
            (
                read("player_motion/data/player_motion/function/accumulate/3.looking.mcfunction"),
                read("player_motion/data/player_motion/function/accumulate/4.motion_set.mcfunction"),
            )
        )
        capture = read(
            "player_motion/data/player_motion/function/accumulate/rotation/"
            "1.execution.mcfunction"
        )

        self.assertIn("compute default float", transforms)
        self.assertIn('type:"sin"', transforms)
        self.assertIn('type:"cos"', transforms)
        self.assertIn("0.017453292519943295", transforms)
        self.assertIn("_.target.x", transforms)
        self.assertIn("_.target.y", transforms)
        self.assertIn("_.target.z", transforms)
        self.assertIn("in neac: as 1604-1604-1604-1604-1604", capture)

    def test_resistance_scales_private_input_before_rotation(self):
        call = read("player_motion/data/player_motion/function/accumulate/1.call.mcfunction")
        looking = "function player_motion:accumulate/3.looking"

        for stage in ("2.explosion", "2.knockback"):
            call_stage = f"function player_motion:accumulate/{stage}"
            self.assertLess(call.index(call_stage), call.index(looking))

            resistance = read(
                "player_motion/data/player_motion/function/accumulate/"
                f"{stage}.mcfunction"
            )
            for axis in "xyz":
                update = (
                    f"data modify storage player_motion: _.in.{axis} "
                    "set compute default float"
                )
                self.assertIn(update, resistance)
                line = next(
                    line for line in resistance.splitlines() if update in line
                )
                self.assertIn(f'path:"_.in.{axis}"', line)
                self.assertNotIn(f"_.calc.{axis} set compute", resistance)

    def test_current_call_multipliers(self):
        multiplier_path = PACK / "data/player_motion/function/accumulate/multiplier"
        functions = {}
        for state in ("in_water", "elytra", "swim"):
            path = multiplier_path / f"{state}.mcfunction"
            self.assertTrue(path.is_file(), f"multiplier/{state}.mcfunction must exist")
            functions[state] = path.read_text(encoding="utf-8")

        water = functions["in_water"]
        self.assertIn("_.in.multiplier.in_water", water)
        water_targets = re.findall(
            r"data modify storage player_motion: _\.target\.([xyz]) set compute",
            water,
        )
        self.assertEqual(water_targets, ["x", "y", "z"])
        for axis in "xyz":
            component_line = next(
                line
                for line in water.splitlines()
                if f"_.target.{axis} set compute" in line
            )
            self.assertIn(f'path:"_.target.{axis}"', component_line)
            self.assertIn('path:"_.in.multiplier.in_water"', component_line)

        for state in ("elytra", "swim"):
            body = functions[state]
            self.assertIn(f"_.in.multiplier.{state}", body)
            self.assertIn("_.target.z", body)
            self.assertNotIn("scoreboard players", body)
            gate_line = next(
                line
                for line in body.splitlines()
                if "execute unless predicate" in line
            )
            self.assertIn('type:"float_value_check"', gate_line)
            self.assertIn('type:"storage"', gate_line)
            self.assertIn('path:"_.target.z"', gate_line)
            self.assertIn('test:{max:0.0f}', gate_line)
            self.assertIn("run data modify", gate_line)
            local_targets = re.findall(
                r"data modify storage player_motion: _\.target\.([xyz]) set compute",
                body,
            )
            self.assertEqual(local_targets, ["z"])
            update_line = next(
                line for line in body.splitlines() if "_.target.z set compute" in line
            )
            self.assertIn('path:"_.target.z"', update_line)
            self.assertIn(f'path:"_.in.multiplier.{state}"', update_line)
            self.assertNotIn("@s PlayerMotion.", body)

        process = read("player_motion/data/player_motion/function/accumulate/4.motion_set.mcfunction")
        pipeline = (
            "function player_motion:accumulate/rotation/2.target",
            "function player_motion:accumulate/multiplier/in_water",
            "function player_motion:accumulate/multiplier/elytra",
            "function player_motion:accumulate/multiplier/swim",
        )
        for call in pipeline:
            self.assertIn(call, process)
        for before, after in zip(pipeline, pipeline[1:]):
            self.assertLess(process.index(before), process.index(after))
        state_flags = {
            "in_water": "is_in_water:true",
            "elytra": "is_fall_flying:true",
            "swim": "is_swimming:true",
        }
        for state, flag in state_flags.items():
            state_line = next(
                line
                for line in process.splitlines()
                if f"function player_motion:accumulate/multiplier/{state}" in line
            )
            self.assertIn(flag, state_line)
            self.assertIn('{type:"entity_properties"', state_line)
            self.assertNotIn("{condition:", state_line)

    def test_end_crystal_geometry(self):
        launch = read_mcfunction_tree("data/player_motion/function/apply")
        summon = read_mcfunction_tree("data/player_motion/function/apply/summon")
        for axis in "xyz":
            self.assertRegex(
                launch,
                rf"store result storage player_motion: _\.launch\.{axis} float 0\.000001 run scoreboard players get @s PlayerMotion\.{axis.upper()}",
            )
        self.assertIn("compute default float", launch)
        for provider in ("sqrt", "div", "floor", "min", "max"):
            self.assertIn(f'type:"{provider}"', launch)
        for literal in ("0.8", "12.0", "_.launch.full_d", "_.launch.d"):
            self.assertIn(literal, launch)
        self.assertIn("# PlayerMotion.X", launch + summon)
        self.assertIn("summon end_crystal run damage @s 0", summon)
        self.assertNotIn("player_motion.internal.", launch + summon)
        self.assertNotIn('type:"entity_eye_height"', launch)
        main = read("player_motion/data/player_motion/function/apply/1.launch.mcfunction")
        self.assertIn("matches 0 if score @s PlayerMotion.Y matches 0 if score @s PlayerMotion.Z matches 0 run return 0", main)
        crystal = read("player_motion/data/player_motion/function/apply/summon/1.crystal.mcfunction")
        self.assertIn("if score # PlayerMotion.Y matches 1", crystal)

    def test_explosion_location(self):
        launch = read_mcfunction_tree("data/player_motion/function/apply")
        summon = read_mcfunction_tree("data/player_motion/function/apply/summon")
        self.assertNotIn("in neac:", launch + summon)
        path = PACK / "data/player_motion/function/apply/4.apply.mcfunction"
        self.assertTrue(path.is_file(), "apply.mcfunction must exist")
        apply = path.read_text(encoding="utf-8")
        for command in (
            "tp ~ ~10000 ~",
            "execute rotated as @s positioned ~ ~10000 ~ run function player_motion:apply/summon/0.main with storage player_motion: _.launch",
            "tp ~ ~ ~",
        ):
            self.assertIn(command, apply)
        self.assertLess(apply.index("tp ~ ~10000 ~"), apply.index("positioned ~ ~10000 ~"))
        self.assertLess(apply.index("positioned ~ ~10000 ~"), apply.index("tp ~ ~ ~"))
        for line in apply.splitlines():
            if "run gamemode" in line or "run function player_motion:apply/gamemode/" in line:
                self.assertIn("if entity @s[type=player]", line)
        self.assertIn("store success score # PlayerMotion.Z", apply)
        self.assertIn("if score # PlayerMotion.Z matches 1 run attribute", apply)
        self.assertIn("-1 add_multiplied_total", apply)
        self.assertIn("modifier remove player_motion:disable_knockback_resistance", apply)

    def test_crystal_distances_match_falloff_and_direction(self):
        # Vertical fixtures have no trigonometry: distance is eye height +/- falloff.
        for vector, count, residual, distance in (
            ((0, 0.4, 0), 0, 0.4, -8.82),
            ((0, -0.4, 0), 0, 0.4, -5.58),
            ((0, 1.6, 0), 2, 0, None),
            ((0.8, 0, 0), 1, 0, None),
        ):
            with self.subTest(vector=vector):
                result = launch_geometry(vector)
                self.assertEqual(result["full_count"], count)
                self.assertAlmostEqual(result["residual"], residual, places=6)
                if distance is not None:
                    self.assertAlmostEqual(result["d"], distance, places=5)
                else:
                    self.assertNotIn("q", result, "zero residual must skip its divisions")

        # The crystal lies on the negative desired direction from the eyes,
        # while its distance from the feet determines explosion falloff.
        for vector in ((0.3, 0.4, 0), (-0.3, -0.4, 0.2), (1e-6, 0, 0), (1024, -1024, 1024)):
            for eye_height in (0.4, 1.27, 1.62):
                with self.subTest(vector=vector, eye_height=eye_height):
                    result = launch_geometry(vector, eye_height)
                    self.assertTrue(all(map(math.isfinite, result.values())))
                    for key, power in (("full_d", 0.8), ("d", result["residual"])):
                        if key not in result:
                            continue
                        d = result[key]
                        feet_distance = math.hypot(d * result["unit_horizontal"], eye_height + d * result["unit_y"])
                        self.assertAlmostEqual(feet_distance, (1 - power) * 12, places=4)

    def test_nonplayer_protection_and_clipped_motion_compensation(self):
        directory = PACK / "data/player_motion/function/apply"
        path = directory / "2.protect.mcfunction"
        self.assertTrue(path.is_file(), "nonplayer protection helper must exist")
        protect = path.read_text(encoding="utf-8")
        main = (directory / "1.launch.mcfunction").read_text(encoding="utf-8")
        player_guard = "execute if entity @s[type=player] run return 0"
        original_guard = "execute if entity @s[nbt={Invulnerable:1b}] run return 0"
        before = "data modify storage player_motion: _.launch.before set from entity @s Motion"
        enable = "execute store success score # PlayerMotion.X run data modify entity @s Invulnerable set value 1b"
        success_guard = "execute unless score # PlayerMotion.X matches 1 run return 0"
        mark = "tag @s add player_motion.restore_invulnerable"
        after = "data modify storage player_motion: _.launch.after set from entity @s Motion"
        order = (player_guard, original_guard, before, enable, success_guard, mark, after)
        for command in order:
            self.assertIn(command, protect)
        for first, second in zip(order, order[1:]):
            self.assertLess(protect.index(first), protect.index(second))
        self.assertIn("execute unless entity @s[type=player] run function player_motion:apply/2.protect", main)
        self.assertLess(main.index("apply/2.protect"), main.index("apply/3.prepare"))
        self.assertIn("execute unless entity @s[type=player] unless entity @s[nbt={Invulnerable:1b}] run return 0", main)
        self.assertIn("execute if score # PlayerMotion.X matches 1 run function player_motion:apply/4.apply", main)
        self.assertGreater(main.index("apply/5.restore_invulnerable"), main.index("apply/4.apply"))

        def evaluate(value, values):
            if value["type"] == "storage":
                return values[value["path"]]
            if value["type"] == "add":
                return sum(evaluate(x, values) for x in value["inputs"])
            self.assertEqual(value["type"], "sub")
            return evaluate(value["left"], values) - evaluate(value["right"], values)

        # The clipped components are recovered; an unchanged component is not doubled.
        for axis, index, requested, before_value, after_value, expected in (
            ("x", 0, 1, 16, 0, 17),
            ("y", 1, 2, -12, 0, -10),
            ("z", 2, 3, 0.25, 0.25, 3),
        ):
            line = next(line for line in protect.splitlines() if f"_.launch.{axis} set compute" in line)
            expression = line.split("compute default float ", 1)[1]
            expression = json.loads(re.sub(r"([,{])([a-z_]+):", r'\1"\2":', expression))
            values = {f"_.launch.{axis}": requested, f"_.launch.before[{index}]": before_value, f"_.launch.after[{index}]": after_value}
            self.assertEqual(evaluate(expression, values), expected)

        prepare = (directory / "3.prepare.mcfunction").read_text(encoding="utf-8")
        zero_guard = "execute if score # PlayerMotion.X matches 0 run return 0"
        self.assertIn(zero_guard, prepare)
        self.assertLess(prepare.index(zero_guard), prepare.index('type:"div"'))

    def test_restore_invulnerable_waits_for_exact_safe_motion(self):
        path = PACK / "data/player_motion/function/apply/5.restore_invulnerable.mcfunction"
        self.assertTrue(path.is_file(), "deferred restoration helper must exist")
        restore = path.read_text(encoding="utf-8")
        lines = [line for line in restore.splitlines() if line and not line.startswith("#")]
        self.assertEqual(lines[:2], [
            "execute if entity @s[type=player] run return 0",
            "execute unless entity @s[tag=player_motion.restore_invulnerable] run return 0",
        ])
        probes = []
        for i, line in enumerate(lines):
            match = re.fullmatch(r"execute store result score # PlayerMotion.X run data get entity @s Motion\[([012])\] (-?1)", line)
            if match:
                probes.append(tuple(map(int, match.groups())))
                self.assertEqual(lines[i + 1], "execute unless score # PlayerMotion.X matches -10..10 run return 0")
        self.assertEqual(probes, [(0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)])
        write = "execute store success score # PlayerMotion.X run data modify entity @s Invulnerable set value 0b"
        remove = "execute if score # PlayerMotion.X matches 1 run tag @s remove player_motion.restore_invulnerable"
        self.assertEqual(lines[-2:], [write, remove])
        # Dual floor probes distinguish adjacent doubles outside +/-10 from the
        # inclusive endpoints, unlike a float32 safety check that rounds to 10.
        for motion, expected in (
            ((10, -10, 0), True), ((0, 0, 0), True),
            ((math.nextafter(10, math.inf), 0, 0), False),
            ((0, math.nextafter(-10, -math.inf), 0), False),
            ((0, 0, 1024), False), ((0, 0, -1024), False),
        ):
            with self.subTest(motion=motion):
                self.assertEqual(all(-10 <= math.floor(motion[axis] * scale) <= 10 for axis, scale in probes), expected)

    def test_passenger_tree_protection(self):
        directory = PACK / "data/player_motion/function/apply/passenger"
        self.assertTrue(directory.is_dir(), "passengers need scoped protection before the root is teleported")
        protect = (directory / "4.protect_tree.mcfunction").read_text(encoding="utf-8")
        restore = (directory / "6.restore_tree.mcfunction").read_text(encoding="utf-8")
        nonplayer = (directory / "5.protect_nonplayer.mcfunction").read_text(encoding="utf-8")
        self.assertIn("execute on passengers run function player_motion:apply/passenger/4.protect_tree", protect)
        self.assertIn("execute on passengers run function player_motion:apply/passenger/6.restore_tree", restore)
        self.assertIn("@s[nbt={Invulnerable:1b}] run return 0", nonplayer)
        self.assertIn("Invulnerable set value 1b", nonplayer)
        self.assertIn("matches 1 run tag @s add player_motion.restore_invulnerable", nonplayer)
        self.assertNotIn("_.launch", nonplayer, "passenger motion must not change the root launch vector")
        resistance = (directory / "1.resistance.mcfunction").read_text(encoding="utf-8")
        self.assertIn("player_motion:passenger_resistance 1 add_value", resistance)
        self.assertIn("matches 1 run tag @s add player_motion.passenger_resistance", resistance)
        self.assertIn("modifier remove player_motion:passenger_resistance", restore)
        self.assertIn("function player_motion:apply/5.restore_invulnerable", restore)
        self.assertIn("if score #passenger_launched PlayerMotion.X matches 1 unless entity @s[type=player] run data modify entity @s Motion set value [0.0d,0.0d,0.0d]", restore)
        for mode in ("survival", "adventure"):
            self.assertIn(f"gamemode={mode}] run tag @s add player_motion.passenger_{mode}", protect)
            self.assertIn(f"tag=player_motion.passenger_{mode}] run gamemode creative @s", protect)
            self.assertIn(f"tag=player_motion.passenger_{mode}] run gamemode {mode} @s", restore)
            self.assertIn(f"tag @s remove player_motion.passenger_{mode}", restore)
        main = read("player_motion/data/player_motion/function/apply/1.launch.mcfunction")
        before = "execute on passengers run function player_motion:apply/passenger/4.protect_tree"
        after = "execute on passengers run function player_motion:apply/passenger/6.restore_tree"
        self.assertLess(main.index(before), main.index("run function player_motion:apply/2.protect"))
        self.assertGreater(main.rindex(after), main.index("run function player_motion:apply/4.apply"))
        self.assertIn("if score #passenger_failed PlayerMotion.X matches 1 run return 0", main)

    def test_passenger_effective_resistance_preflight(self):
        directory = PACK / "data/player_motion/function/apply/passenger"
        preflight = directory / "0.prepare_tree.mcfunction"
        self.assertTrue(preflight.is_file(), "resistance must be checked before root or rider protection mutates entity state")
        prepare = preflight.read_text(encoding="utf-8")
        resistance = (directory / "1.resistance.mcfunction").read_text(encoding="utf-8")
        boost = (directory / "3.boost.mcfunction").read_text(encoding="utf-8")
        restore = (directory / "6.restore_tree.mcfunction").read_text(encoding="utf-8")
        main = read("player_motion/data/player_motion/function/apply/1.launch.mcfunction")
        apply = read("player_motion/data/player_motion/function/apply/4.apply.mcfunction")
        self.assertIn("execute on passengers run function player_motion:apply/passenger/0.prepare_tree", prepare)
        self.assertNotIn("data modify entity", prepare + resistance)
        exact_probe = "execute store result score # PlayerMotion.X run attribute @s explosion_knockback_resistance get"
        self.assertIn(exact_probe, resistance)
        self.assertGreater(resistance.rindex(exact_probe), resistance.index("function player_motion:apply/passenger/2.prepare_boost"))
        self.assertIn("unless score # PlayerMotion.X matches 1 run scoreboard players set #passenger_failed PlayerMotion.X 1", resistance)
        self.assertIn("player_motion:passenger_resistance_boost $(boost) add_multiplied_total", boost)
        self.assertIn("modifier remove player_motion:passenger_resistance_boost", restore)
        self.assertIn("tag @s remove player_motion.passenger_resistance_boost", restore)
        abort = "execute if score #passenger_failed PlayerMotion.X matches 1 run return 0"
        self.assertLess(main.index(abort), main.index("run function player_motion:apply/2.protect"))
        self.assertLess(main.index(abort), main.index("on passengers run function player_motion:apply/passenger/4.protect_tree"))
        self.assertIn("scoreboard players set #passenger_launched PlayerMotion.X 0", main)
        self.assertLess(apply.index("scoreboard players set #passenger_launched PlayerMotion.X 1"), apply.index("tp ~ ~10000 ~"))

    def test_tick_flush_and_cleanup(self):
        tick = read(
            "player_motion/data/player_motion/function/schedule_tick.mcfunction"
        )
        commands = [
            line
            for line in tick.splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(
            commands,
            [
                "schedule function player_motion:schedule_tick 1t replace",
                "execute as @a at @s run function player_motion:apply/0.flush",
            ],
        )

        flush_dimension = read(
            "player_motion/data/player_motion/function/apply/0.flush.mcfunction"
        )
        flush_commands = [
            line
            for line in flush_dimension.splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(
            flush_commands,
            [
                "execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/1.launch",
                "execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/6.cleanup",
                "execute as @e[type=!player,tag=player_motion.restore_invulnerable,distance=0..] run function player_motion:apply/5.restore_invulnerable",
                "scoreboard players reset #",
                "scoreboard players reset #passenger_failed",
                "scoreboard players reset #passenger_launched",
            ],
        )

        cleanup_path = (
            PACK
            / "data/player_motion/function/apply/6.cleanup.mcfunction"
        )
        self.assertTrue(cleanup_path.is_file(), "launch cleanup must exist")
        cleanup = [
            line
            for line in cleanup_path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        self.assertEqual(
            cleanup,
            [
                "scoreboard players reset @s PlayerMotion.X",
                "scoreboard players reset @s PlayerMotion.Y",
                "scoreboard players reset @s PlayerMotion.Z",
                "tag @s remove player_motion.pending",
            ],
        )

    def test_flush_revalidates_current_player_eligibility_before_mutation(self):
        main = read(
            "player_motion/data/player_motion/function/apply/1.launch.mcfunction"
        )
        commands = [
            line
            for line in main.splitlines()
            if line and not line.startswith("#")
        ]
        guards = [
            "execute if entity @s[type=player,gamemode=spectator] run return 0",
            "execute if entity @s[type=player,gamemode=creative] if predicate {type:\"entity_properties\",entity:\"this\",predicate:{flags:{is_flying:true,is_fall_flying:false}}} run return 0",
            "execute if entity @s[type=player] on vehicle run return 0",
        ]
        self.assertEqual(
            commands[:3],
            guards,
            "flush-time player guards must run before launch storage, protection, "
            "gamemode, position, or passenger state can change",
        )
        self.assertTrue(
            all("type=player" in guard for guard in guards),
            "current-player guards must not reject root vehicle targets",
        )

        flush = read(
            "player_motion/data/player_motion/function/apply/0.flush.mcfunction"
        )
        self.assertLess(
            flush.index("run function player_motion:apply/1.launch"),
            flush.index("run function player_motion:apply/6.cleanup"),
            "the wrapper must clean queued scores/tags even when launch returns early",
        )

    def test_old_api_removed(self):
        api = PACK / "data/player_motion/function/api"
        self.assertFalse((api / "launch_xyz.mcfunction").exists())
        self.assertFalse((api / "launch_looking.mcfunction").exists())
        public_runtime = all_mcfunctions() + read("README.md")
        for obsolete in (
            "$function_called",
            "player_motion.launch",
            "player_motion.api.launch",
        ):
            self.assertNotIn(obsolete, public_runtime)

    def test_fixed_point_saturation(self):
        path = PACK / "data/player_motion/function/accumulate/5.score.mcfunction"
        self.assertTrue(path.is_file(), "accumulate/5.score.mcfunction must exist")
        accumulate = path.read_text(encoding="utf-8")

        for literal in ("1000000", "1024000000", "-1024000000"):
            self.assertIn(literal, accumulate)
        for axis, objective in (("x", "X"), ("y", "Y"), ("z", "Z")):
            store = (
                f"execute store result score # PlayerMotion.{objective} "
                "run compute default float"
            )
            add = (
                f"scoreboard players operation @s PlayerMotion.{objective} "
                f"+= # PlayerMotion.{objective}"
            )
            upper = (
                f"execute if score @s PlayerMotion.{objective} matches 1024000001.. "
                f"run scoreboard players set @s PlayerMotion.{objective} 1024000000"
            )
            lower = (
                f"execute if score @s PlayerMotion.{objective} matches ..-1024000001 "
                f"run scoreboard players set @s PlayerMotion.{objective} -1024000000"
            )
            self.assertIn(store, accumulate)
            component_line = next(line for line in accumulate.splitlines() if store in line)
            self.assertIn(f'path:"_.calc.{axis}"', component_line)
            self.assertIn('type:"min"', component_line)
            self.assertIn('type:"max"', component_line)
            self.assertIn('type:"round"', component_line)
            for literal in ("-1024.0", "1024.0", "1000000.0"):
                self.assertIn(literal, component_line)
            self.assertLess(accumulate.index(store), accumulate.index(add))
            self.assertLess(accumulate.index(add), accumulate.index(upper))
            self.assertLess(accumulate.index(add), accumulate.index(lower))
            self.assertIn(upper, accumulate)
            self.assertIn(lower, accumulate)

        queue_commands = re.findall(
            r"^tag @s add \S+", accumulate, re.MULTILINE
        )
        self.assertEqual(queue_commands, ["tag @s add player_motion.pending"])
        self.assertGreater(
            accumulate.index("tag @s add player_motion.pending"),
            accumulate.index("..-1024000001"),
        )


if __name__ == "__main__":
    unittest.main()
