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


def read_mcfunction_tree(relative: str) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((PACK / relative).rglob("*.mcfunction"))
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
