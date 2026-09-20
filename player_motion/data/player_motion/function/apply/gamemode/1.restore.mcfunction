# Called only for players after returning to the original execution position.
execute if score #mode PlayerMotion.X matches 0 run return run gamemode survival @s
execute if score #mode PlayerMotion.X matches 1 run return run gamemode creative @s
execute if score #mode PlayerMotion.X matches 2 run gamemode adventure @s
