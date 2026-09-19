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


if __name__ == "__main__":
    unittest.main()
