# A root teleport also carries its passenger tree into the explosion area.
scoreboard players set #passenger_failed PlayerMotion.X 0
execute on passengers run function player_motion:internal/launch/passenger/protect_tree
execute if score #passenger_failed PlayerMotion.X matches 1 on passengers run function player_motion:internal/launch/passenger/restore_tree
execute if score #passenger_failed PlayerMotion.X matches 1 run return 0

# Non-living vehicles have no Health tag and skip attribute handling.
# Record successful addition so an absent attribute cannot affect restoration.
scoreboard players set #resistance PlayerMotion.X 0
execute if data entity @s Health store success score #resistance PlayerMotion.X run attribute @s minecraft:explosion_knockback_resistance modifier add player_motion:disable_knockback_resistance -1 add_multiplied_total
execute if entity @s[type=minecraft:player] run function player_motion:internal/launch/gamemode/get
execute if entity @s[type=minecraft:player] run gamemode creative @s

# Keep the original command position as the anchor in the current dimension.
tp ~ ~10000 ~
execute rotated as @s positioned ~ ~10000 ~ run function player_motion:internal/summon/main with storage player_motion: _.launch
tp ~ ~ ~

execute if entity @s[type=minecraft:player] run function player_motion:internal/launch/gamemode/restore
execute if score #resistance PlayerMotion.X matches 1 run attribute @s minecraft:explosion_knockback_resistance modifier remove player_motion:disable_knockback_resistance
execute on passengers run function player_motion:internal/launch/passenger/restore_tree
