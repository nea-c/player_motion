$execute store success score # PlayerMotion.X run attribute @s explosion_knockback_resistance modifier add player_motion:passenger_resistance_boost $(boost) add_multiplied_total
execute if score # PlayerMotion.X matches 1 run tag @s add player_motion.passenger_resistance_boost
