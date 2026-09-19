# Save only modes changed by this invocation. Originally creative/spectator riders stay as-is.
execute if entity @s[type=minecraft:player,gamemode=survival] run tag @s add player_motion.passenger_survival
execute if entity @s[type=minecraft:player,gamemode=adventure] run tag @s add player_motion.passenger_adventure
execute if entity @s[type=minecraft:player,tag=player_motion.passenger_survival] run gamemode creative @s
execute if entity @s[type=minecraft:player,tag=player_motion.passenger_adventure] run gamemode creative @s
execute if entity @s[type=minecraft:player,gamemode=!creative,gamemode=!spectator] run scoreboard players set #passenger_failed PlayerMotion.X 1
execute unless entity @s[type=minecraft:player] run function player_motion:internal/launch/passenger/protect_nonplayer

# Full resistance prevents the synthetic impulse from becoming a rider's own velocity.
# Unsupported attributes fail without an ownership tag; an existing same-id modifier is preserved.
execute store success score #passenger_has_resistance PlayerMotion.X run attribute @s minecraft:explosion_knockback_resistance get
execute unless entity @s[type=minecraft:player] unless score #passenger_has_resistance PlayerMotion.X matches 1 run tag @s add player_motion.passenger_clear_motion
execute store success score #passenger_resistance PlayerMotion.X run attribute @s minecraft:explosion_knockback_resistance modifier add player_motion:passenger_resistance 1 add_value
execute if score #passenger_resistance PlayerMotion.X matches 1 run tag @s add player_motion.passenger_resistance
execute on passengers run function player_motion:internal/launch/passenger/protect_tree
