# Consume the saturated global vector. Tick owns pending-tag/score cleanup.
data modify storage player_motion: _.launch set value {}
execute store result storage player_motion: _.launch.x float 0.000001 run scoreboard players get @s PlayerMotion.X
execute store result storage player_motion: _.launch.y float 0.000001 run scoreboard players get @s PlayerMotion.Y
execute store result storage player_motion: _.launch.z float 0.000001 run scoreboard players get @s PlayerMotion.Z
# A zero vector has no direction and must not reach normalization or summon.
execute if score @s PlayerMotion.X matches 0 if score @s PlayerMotion.Y matches 0 if score @s PlayerMotion.Z matches 0 run return 0
function player_motion:internal/launch/prepare
function player_motion:internal/launch/apply
