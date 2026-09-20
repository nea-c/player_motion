$execute store success score #player_motion PlayerMotion.X run attribute @s explosion_knockback_resistance modifier add player_motion:passenger_resistance_boost $(boost) add_multiplied_total
execute if score #player_motion PlayerMotion.X matches 1 run tag @s add player_motion.passenger_resistance_boost
