# Players use creative mode. Preserve targets already invulnerable without writes.
execute if entity @s[type=minecraft:player] run return 0
execute if entity @s[nbt={Invulnerable:1b}] run return 0

# Entity.load clips Motion components outside +/-10 when enabling protection.
# Snapshot both sides and add only that lost motion to the requested impulse.
data modify storage player_motion: _.launch.before set from entity @s Motion
execute store success score #protected PlayerMotion.X run data modify entity @s Invulnerable set value 1b
execute unless score #protected PlayerMotion.X matches 1 run return 0
tag @s add player_motion.restore_invulnerable
data modify storage player_motion: _.launch.after set from entity @s Motion
data modify storage player_motion: _.launch.x set compute default float {type:"minecraft:add",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.x"},{type:"minecraft:sub",left:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.before[0]"},right:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.after[0]"}}]}
data modify storage player_motion: _.launch.y set compute default float {type:"minecraft:add",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.y"},{type:"minecraft:sub",left:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.before[1]"},right:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.after[1]"}}]}
data modify storage player_motion: _.launch.z set compute default float {type:"minecraft:add",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.z"},{type:"minecraft:sub",left:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.before[2]"},right:{type:"minecraft:storage",storage:"player_motion:",path:"_.launch.after[2]"}}]}
