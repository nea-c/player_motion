# Missing attributes behave as zero resistance, which keeps non-living vehicles usable.
data modify storage player_motion: _.resistance set value 0.0f
execute store result storage player_motion: _.resistance float 0.000001 run attribute @s explosion_knockback_resistance get 1000000
data modify storage player_motion: _.resistance set compute default float {type:"max",inputs:[{type:"sub",left:1.0,right:{type:"storage",storage:"player_motion:",path:"_.resistance"}},0.0]}

data modify storage player_motion: _.in.x set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.x"},{type:"storage",storage:"player_motion:",path:"_.resistance"}]}
data modify storage player_motion: _.in.y set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.y"},{type:"storage",storage:"player_motion:",path:"_.resistance"}]}
data modify storage player_motion: _.in.z set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.z"},{type:"storage",storage:"player_motion:",path:"_.resistance"}]}
