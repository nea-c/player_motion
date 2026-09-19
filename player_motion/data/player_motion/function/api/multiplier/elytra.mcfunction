# Scale only forward target-local motion while the target is fall-flying.
execute store result score #sign PlayerMotion.Z run compute default float {type:"minecraft:sign",input:{type:"minecraft:storage",storage:"player_motion:",path:"_.target.z"}}
execute if score #sign PlayerMotion.Z matches 1 run data modify storage player_motion: _.target.z set compute default float {type:"minecraft:mul",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.target.z"},{type:"minecraft:storage",storage:"player_motion:",path:"_.in.multiplier.elytra"}]}
