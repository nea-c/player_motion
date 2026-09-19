# Called only for players. Spectators are rejected by the public API.
scoreboard players set #mode PlayerMotion.X -1
execute if entity @s[gamemode=survival] run return run scoreboard players set #mode PlayerMotion.X 0
execute if entity @s[gamemode=creative] run return run scoreboard players set #mode PlayerMotion.X 1
execute if entity @s[gamemode=adventure] run scoreboard players set #mode PlayerMotion.X 2
