# Passenger protection must not contribute clipped rider motion to the root vector.
execute if entity @s[nbt={Invulnerable:1b}] run return 0
execute store success score # PlayerMotion.X run data modify entity @s Invulnerable set value 1b
execute if score # PlayerMotion.X matches 1 run tag @s add player_motion.restore_invulnerable
execute unless entity @s[nbt={Invulnerable:1b}] run scoreboard players set #passenger_failed PlayerMotion.X 1
