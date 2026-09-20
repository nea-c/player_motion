# Own only modifiers successfully added by this call; preserve all existing modifiers/base.
execute store success score # PlayerMotion.X run attribute @s explosion_knockback_resistance modifier add player_motion:passenger_resistance 1 add_value
execute if score # PlayerMotion.X matches 1 run tag @s add player_motion.passenger_resistance

# This attribute is clamped to [0,1]. Its unscaled integer result is 1 only at full resistance.
execute store result score # PlayerMotion.X run attribute @s explosion_knockback_resistance get
execute if score # PlayerMotion.X matches 1 run return 0

# Measure a conservative lower bound. Zero (including a -1 total modifier) cannot be boosted.
execute store result score # PlayerMotion.X run attribute @s explosion_knockback_resistance get 1000000000
execute if score # PlayerMotion.X matches 1.. run function player_motion:apply/passenger/2.prepare_boost
execute store result score # PlayerMotion.X run attribute @s explosion_knockback_resistance get
execute unless score # PlayerMotion.X matches 1 run scoreboard players set #passenger_failed PlayerMotion.X 1
