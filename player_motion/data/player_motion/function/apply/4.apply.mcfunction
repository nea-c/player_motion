# Non-living vehicles have no Health tag and skip attribute handling.
# Record successful addition so an absent attribute cannot affect restoration.
scoreboard players set #player_motion PlayerMotion.Z 0
execute if data entity @s Health store success score #player_motion PlayerMotion.Z run attribute @s explosion_knockback_resistance modifier add player_motion:disable_knockback_resistance -1 add_multiplied_total
execute if entity @s[type=player] run function player_motion:apply/gamemode/0.get
execute if entity @s[type=player] run gamemode creative @s

# Keep the original command position as the anchor in the current dimension.
scoreboard players set #player_motion.passenger_launched PlayerMotion.X 1
tp ~ ~10000 ~
execute rotated as @s positioned ~ ~10000 ~ run function player_motion:apply/summon/0.main with storage player_motion: _.launch
tp ~ ~ ~

execute if entity @s[type=player] run function player_motion:apply/gamemode/1.restore
execute if score #player_motion PlayerMotion.Z matches 1 run attribute @s explosion_knockback_resistance modifier remove player_motion:disable_knockback_resistance
