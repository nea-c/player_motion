# Save only modes changed by this invocation. Originally creative/spectator riders stay as-is.
execute if entity @s[type=player,gamemode=survival] run tag @s add player_motion.passenger_survival
execute if entity @s[type=player,gamemode=adventure] run tag @s add player_motion.passenger_adventure
execute if entity @s[type=player,tag=player_motion.passenger_survival] run gamemode creative @s
execute if entity @s[type=player,tag=player_motion.passenger_adventure] run gamemode creative @s
execute if entity @s[type=player,gamemode=!creative,gamemode=!spectator] run scoreboard players set #passenger_failed PlayerMotion.X 1
execute unless entity @s[type=player] run function player_motion:internal/launch/passenger/protect_nonplayer

execute on passengers run function player_motion:internal/launch/passenger/protect_tree
