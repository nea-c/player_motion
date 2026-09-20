# Called only for players after returning to the original execution position.
execute if data storage player_motion: _.launch{mode:0} run return run gamemode survival @s
execute if data storage player_motion: _.launch{mode:1} run return run gamemode creative @s
execute if data storage player_motion: _.launch{mode:2} run gamemode adventure @s
