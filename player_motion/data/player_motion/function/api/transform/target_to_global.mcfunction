# Build the target's forward rotation matrix.
data modify storage player_motion: _.transform.sin_pitch set compute default float {type:"sin",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target_rotation[1]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.cos_pitch set compute default float {type:"cos",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target_rotation[1]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.sin_yaw set compute default float {type:"sin",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target_rotation[0]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.cos_yaw set compute default float {type:"cos",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target_rotation[0]"},0.017453292519943295]}}

# tmp = target.y*sin(pitch) + target.z*cos(pitch)
data modify storage player_motion: _.transform.tmp set compute default float {type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.y"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_pitch"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.z"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_pitch"}]}]}

# global.x = target.x*cos(yaw) - tmp*sin(yaw)
data modify storage player_motion: _.calc.x set compute default float {type:"sub",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.x"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_yaw"}]},right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.transform.tmp"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_yaw"}]}}
# global.y = target.y*cos(pitch) - target.z*sin(pitch)
data modify storage player_motion: _.calc.y set compute default float {type:"sub",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.y"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_pitch"}]},right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.z"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_pitch"}]}}
# global.z = target.x*sin(yaw) + tmp*cos(yaw)
data modify storage player_motion: _.calc.z set compute default float {type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.target.x"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_yaw"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.transform.tmp"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_yaw"}]}]}
