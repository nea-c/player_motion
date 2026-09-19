# Consume the saturated global vector. Tick owns pending-tag/score cleanup.
data modify storage player_motion: _.launch set value {}
execute store result storage player_motion: _.launch.x float 0.000001 run scoreboard players get @s PlayerMotion.X
execute store result storage player_motion: _.launch.y float 0.000001 run scoreboard players get @s PlayerMotion.Y
execute store result storage player_motion: _.launch.z float 0.000001 run scoreboard players get @s PlayerMotion.Z
# A zero vector has no direction and must not reach normalization or summon.
execute if score @s PlayerMotion.X matches 0 if score @s PlayerMotion.Y matches 0 if score @s PlayerMotion.Z matches 0 run return 0

# Preflight all riders before any NBT protection write can clip the root's existing Motion.
scoreboard players set #passenger_failed PlayerMotion.X 0
scoreboard players set #passenger_launched PlayerMotion.X 0
execute on passengers run function player_motion:internal/launch/passenger/prepare_tree
execute if score #passenger_failed PlayerMotion.X matches 1 on passengers run function player_motion:internal/launch/passenger/restore_tree
execute if score #passenger_failed PlayerMotion.X matches 1 run return 0
execute on passengers run function player_motion:internal/launch/passenger/protect_tree
execute if score #passenger_failed PlayerMotion.X matches 1 on passengers run function player_motion:internal/launch/passenger/restore_tree
execute if score #passenger_failed PlayerMotion.X matches 1 run return 0

execute unless entity @s[type=minecraft:player] run function player_motion:internal/launch/protect
# Do not expose a nonplayer if enabling protection failed.
execute unless entity @s[type=minecraft:player] unless entity @s[nbt={Invulnerable:1b}] on passengers run function player_motion:internal/launch/passenger/restore_tree
execute unless entity @s[type=minecraft:player] unless entity @s[nbt={Invulnerable:1b}] run return 0
function player_motion:internal/launch/prepare
execute if score #magnitude PlayerMotion.X matches 1 run function player_motion:internal/launch/apply
execute on passengers run function player_motion:internal/launch/passenger/restore_tree
# A clipped-motion correction can cancel the requested impulse. Restore in that
# case too; unsafe post-launch motion leaves the tag for the recurring tick.
execute if entity @s[type=!minecraft:player,tag=player_motion.restore_invulnerable] run function player_motion:internal/launch/restore_invulnerable
