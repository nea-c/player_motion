# Scale only forward target-local motion while the target is fall-flying.
execute store result score # PlayerMotion.Z run compute default float {type:"ceil",input:{type:"min",inputs:[{type:"max",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.z"},0.0]},1.0]}}
execute if score # PlayerMotion.Z matches 1 run data modify storage player_motion: _.target.z set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.z"},{type:"storage",storage:"player_motion:",path:"_.in.multiplier.elytra"}]}
scoreboard players reset # PlayerMotion.Z
