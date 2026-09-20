# Restore descendants before their parent; no root launch scratch storage is touched.
execute on passengers run function player_motion:apply/passenger/6.restore_tree
# Match vanilla rideTick for every nonplayer after a blast, regardless of attributes.
# A failed preflight has not blasted or changed root motion and must not clear rider motion.
execute if score #player_motion.passenger_launched PlayerMotion.X matches 1 unless entity @s[type=player] run data modify entity @s Motion set value [0.0d,0.0d,0.0d]
execute if entity @s[tag=player_motion.passenger_resistance_boost] run attribute @s explosion_knockback_resistance modifier remove player_motion:passenger_resistance_boost
tag @s remove player_motion.passenger_resistance_boost
execute if entity @s[tag=player_motion.passenger_resistance] run attribute @s explosion_knockback_resistance modifier remove player_motion:passenger_resistance
tag @s remove player_motion.passenger_resistance
execute if entity @s[type=player,tag=player_motion.passenger_survival] run gamemode survival @s
execute if entity @s[type=player,tag=player_motion.passenger_adventure] run gamemode adventure @s
tag @s remove player_motion.passenger_survival
tag @s remove player_motion.passenger_adventure
execute unless entity @s[type=player] run function player_motion:apply/5.restore_invulnerable
