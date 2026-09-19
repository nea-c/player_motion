import json
import math
import re
import struct
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
        kind = provider["type"].removeprefix("minecraft:")
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

    source = read("player_motion/data/player_motion/function/internal/launch/prepare.mcfunction")
    for line in source.splitlines():
        match = re.search(r"_\.launch\.(\w+) set compute default float (.+)$", line)
        if not match:
            continue
        if line.startswith("execute if score #residual") and values["residual"] == 0:
            continue
        name, expression = match.groups()
        expression = re.sub(r"([,{])([a-z_]+):", r'\1"\2":', expression)
        values[name] = evaluate(json.loads(expression))
    return values


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

    def test_api_defaults_and_fields(self):
        call_path = PACK / "data/player_motion/function/api/call.mcfunction"
        self.assertTrue(call_path.is_file(), "api/call.mcfunction must exist")
        for relative in (
            "process.mcfunction",
            "resistance/knockback.mcfunction",
            "resistance/explosion.mcfunction",
        ):
            self.assertTrue(
                (call_path.parent / relative).is_file(), f"api/{relative} must exist"
            )
        call = read("player_motion/data/player_motion/function/api/call.mcfunction")
        api = read_mcfunction_tree("data/player_motion/function/api")

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
        self.assertIn("minecraft:knockback_resistance", api)
        self.assertIn("minecraft:explosion_knockback_resistance", api)
        self.assertIn("get 1000000", api)
        self.assertIn("float 0.000001", api)
        self.assertLess(
            call.index("internal/rotation/capture_execution"),
            call.index("api/process"),
        )

    def test_rotation_and_float_transforms(self):
        transform_path = PACK / "data/player_motion/function/api/transform"
        capture_path = (
            PACK
            / "data/player_motion/function/internal/rotation/capture_execution.mcfunction"
        )
        self.assertTrue(transform_path.is_dir(), "transform functions must exist")
        self.assertTrue(capture_path.is_file(), "capture_execution.mcfunction must exist")
        for relative in (
            "execution_to_global.mcfunction",
            "global_to_target.mcfunction",
            "target_to_global.mcfunction",
        ):
            self.assertTrue(
                (transform_path / relative).is_file(),
                f"transform/{relative} must exist",
            )
        for relative in ("capture_target.mcfunction", "get.mcfunction"):
            self.assertTrue(
                (capture_path.parent / relative).is_file(),
                f"internal/rotation/{relative} must exist",
            )
        transforms = read_mcfunction_tree(
            "data/player_motion/function/api/transform"
        )
        capture = read(
            "player_motion/data/player_motion/function/internal/rotation/"
            "capture_execution.mcfunction"
        )

        self.assertIn("compute default float", transforms)
        self.assertIn('type:"minecraft:sin"', transforms)
        self.assertIn('type:"minecraft:cos"', transforms)
        self.assertIn("0.017453292519943295", transforms)
        self.assertIn("_.target.x", transforms)
        self.assertIn("_.target.y", transforms)
        self.assertIn("_.target.z", transforms)
        self.assertIn("in neac: as 1604-1604-1604-1604-1604", capture)

    def test_current_call_multipliers(self):
        multiplier_path = PACK / "data/player_motion/function/api/multiplier"
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
            self.assertNotIn('type:"minecraft:sign"', body)
            self.assertIn(
                "execute store result score #positive PlayerMotion.Z", body
            )
            gate_line = next(
                line
                for line in body.splitlines()
                if "execute store result score #positive PlayerMotion.Z" in line
            )
            self.assertIn('type:"minecraft:ceil"', gate_line)
            self.assertIn('type:"minecraft:min"', gate_line)
            self.assertIn('type:"minecraft:max"', gate_line)
            self.assertIn('path:"_.target.z"', gate_line)
            self.assertIn("0.0", gate_line)
            self.assertIn("1.0", gate_line)
            self.assertRegex(body, r"matches 1(?:\.\.)? run data modify")
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

        process = read("player_motion/data/player_motion/function/api/process.mcfunction")
        pipeline = (
            "function player_motion:api/transform/global_to_target",
            "function player_motion:api/multiplier/in_water",
            "function player_motion:api/multiplier/elytra",
            "function player_motion:api/multiplier/swim",
            "function player_motion:api/transform/target_to_global",
            "function player_motion:api/accumulate",
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
                if f"function player_motion:api/multiplier/{state}" in line
            )
            self.assertIn(flag, state_line)
            self.assertIn('{type:"minecraft:entity_properties"', state_line)
            self.assertNotIn("{condition:", state_line)

    def test_end_crystal_geometry(self):
        launch = read_mcfunction_tree("data/player_motion/function/internal/launch")
        summon = read_mcfunction_tree("data/player_motion/function/internal/summon")
        for axis in "xyz":
            self.assertRegex(
                launch,
                rf"store result storage player_motion: _\.launch\.{axis} float 0\.000001 run scoreboard players get @s PlayerMotion\.{axis.upper()}",
            )
        self.assertIn("compute default float", launch)
        for provider in ("sqrt", "div", "floor", "min", "max"):
            self.assertIn(f'type:"minecraft:{provider}"', launch)
        for literal in ("0.8", "12.0", "_.launch.full_d", "_.launch.d"):
            self.assertIn(literal, launch)
        self.assertIn("#full_count PlayerMotion.X", launch + summon)
        self.assertIn("summon end_crystal run damage @s 0", summon)
        self.assertNotIn("player_motion.internal.", launch + summon)
        self.assertNotIn('type:"minecraft:entity_eye_height"', launch)
        main = read("player_motion/data/player_motion/function/internal/launch/main.mcfunction")
        self.assertIn("matches 0 if score @s PlayerMotion.Y matches 0 if score @s PlayerMotion.Z matches 0 run return 0", main)
        crystal = read("player_motion/data/player_motion/function/internal/summon/crystal.mcfunction")
        self.assertIn("if score #residual PlayerMotion.X matches 1", crystal)

    def test_explosion_location(self):
        launch = read_mcfunction_tree("data/player_motion/function/internal/launch")
        summon = read_mcfunction_tree("data/player_motion/function/internal/summon")
        self.assertNotIn("in neac:", launch + summon)
        path = PACK / "data/player_motion/function/internal/launch/apply.mcfunction"
        self.assertTrue(path.is_file(), "apply.mcfunction must exist")
        apply = path.read_text(encoding="utf-8")
        for command in (
            "tp ~ ~10000 ~",
            "execute rotated as @s positioned ~ ~10000 ~ run function player_motion:internal/summon/main with storage player_motion: _.launch",
            "tp ~ ~ ~",
        ):
            self.assertIn(command, apply)
        self.assertLess(apply.index("tp ~ ~10000 ~"), apply.index("positioned ~ ~10000 ~"))
        self.assertLess(apply.index("positioned ~ ~10000 ~"), apply.index("tp ~ ~ ~"))
        for line in apply.splitlines():
            if "run gamemode" in line or "run function player_motion:internal/launch/gamemode/" in line:
                self.assertIn("if entity @s[type=minecraft:player]", line)
        self.assertIn("store success score #resistance PlayerMotion.X", apply)
        self.assertIn("if score #resistance PlayerMotion.X matches 1 run attribute", apply)
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

    def test_fixed_point_saturation(self):
        path = PACK / "data/player_motion/function/api/accumulate.mcfunction"
        self.assertTrue(path.is_file(), "api/accumulate.mcfunction must exist")
        accumulate = path.read_text(encoding="utf-8")

        for literal in ("1000000", "1024000000", "-1024000000"):
            self.assertIn(literal, accumulate)
        for axis, objective in (("x", "X"), ("y", "Y"), ("z", "Z")):
            store = (
                f"execute store result score #delta PlayerMotion.{objective} "
                "run compute default float"
            )
            add = (
                f"scoreboard players operation @s PlayerMotion.{objective} "
                f"+= #delta PlayerMotion.{objective}"
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
            self.assertIn('type:"minecraft:min"', component_line)
            self.assertIn('type:"minecraft:max"', component_line)
            self.assertIn('type:"minecraft:round"', component_line)
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
