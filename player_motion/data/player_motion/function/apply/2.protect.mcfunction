# Players use creative mode. Check original invulnerability once and cache safety in storage.
execute if entity @s[type=player] run return fail
data modify storage player_motion: _.Invulnerable set value true
execute if predicate {type:"entity_properties",entity:"this",predicate:{nbt:{Invulnerable:true}}} run return fail

# Entity.load clips Motion components outside +/-10 when enabling protection.
# Snapshot both sides and add only that lost motion to the requested impulse.
data modify storage player_motion: _.launch.before set from entity @s Motion
execute store success storage player_motion: _.Invulnerable byte 1 run data modify entity @s Invulnerable set value 1b
execute unless data storage player_motion: _{Invulnerable:true} run return fail
tag @s add player_motion.restore_invulnerable
data modify storage player_motion: _.launch.after set from entity @s Motion
data modify storage player_motion: _.launch.x set compute default float {type:"add",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.x"},{type:"sub",left:{type:"storage",storage:"player_motion:",path:"_.launch.before[0]"},right:{type:"storage",storage:"player_motion:",path:"_.launch.after[0]"}}]}
data modify storage player_motion: _.launch.y set compute default float {type:"add",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.y"},{type:"sub",left:{type:"storage",storage:"player_motion:",path:"_.launch.before[1]"},right:{type:"storage",storage:"player_motion:",path:"_.launch.after[1]"}}]}
data modify storage player_motion: _.launch.z set compute default float {type:"add",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.z"},{type:"sub",left:{type:"storage",storage:"player_motion:",path:"_.launch.before[2]"},right:{type:"storage",storage:"player_motion:",path:"_.launch.after[2]"}}]}
