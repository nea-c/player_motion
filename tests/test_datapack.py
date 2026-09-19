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
