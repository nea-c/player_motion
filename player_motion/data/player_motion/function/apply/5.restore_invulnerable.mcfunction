# Call after launch and retry each tick for tagged entities in every dimension.
# Never rewrite players or targets whose original invulnerability we did not change.
execute if entity @s[type=player] run return 0
execute unless entity @s[tag=player_motion.restore_invulnerable] run return 0

# Entity.load preserves Motion only within inclusive +/-10. Two exact double
# floor probes avoid float rounding at the boundary; unsafe targets keep the tag.
execute store result score # PlayerMotion.X run data get entity @s Motion[0] 1
execute unless score # PlayerMotion.X matches -10..10 run return 0
execute store result score # PlayerMotion.X run data get entity @s Motion[0] -1
execute unless score # PlayerMotion.X matches -10..10 run return 0
execute store result score # PlayerMotion.X run data get entity @s Motion[1] 1
execute unless score # PlayerMotion.X matches -10..10 run return 0
execute store result score # PlayerMotion.X run data get entity @s Motion[1] -1
execute unless score # PlayerMotion.X matches -10..10 run return 0
execute store result score # PlayerMotion.X run data get entity @s Motion[2] 1
execute unless score # PlayerMotion.X matches -10..10 run return 0
execute store result score # PlayerMotion.X run data get entity @s Motion[2] -1
execute unless score # PlayerMotion.X matches -10..10 run return 0

execute store success score # PlayerMotion.X run data modify entity @s Invulnerable set value 0b
execute if score # PlayerMotion.X matches 1 run tag @s remove player_motion.restore_invulnerable
