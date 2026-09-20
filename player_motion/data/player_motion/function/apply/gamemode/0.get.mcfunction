# Called only for players. Spectators are rejected by the public API.
data modify storage player_motion: _.launch.mode set value -1
execute if entity @s[gamemode=survival] run return run data modify storage player_motion: _.launch.mode set value 0
execute if entity @s[gamemode=creative] run return run data modify storage player_motion: _.launch.mode set value 1
execute if entity @s[gamemode=adventure] run data modify storage player_motion: _.launch.mode set value 2
