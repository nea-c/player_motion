# Scale every target-local component of this call while the target is in water.
data modify storage player_motion: _.target.x set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.x"},{type:"storage",storage:"player_motion:",path:"_.in.multiplier.in_water"}]}
data modify storage player_motion: _.target.y set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.y"},{type:"storage",storage:"player_motion:",path:"_.in.multiplier.in_water"}]}
data modify storage player_motion: _.target.z set compute default float {type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.z"},{type:"storage",storage:"player_motion:",path:"_.in.multiplier.in_water"}]}
