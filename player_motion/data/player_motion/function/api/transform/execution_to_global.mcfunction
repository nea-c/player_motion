# Convert the original command rotation from degrees to radians.
data modify storage player_motion: _.transform.sin_pitch set compute default float {type:"sin",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.execution_rotation[1]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.cos_pitch set compute default float {type:"cos",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.execution_rotation[1]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.sin_yaw set compute default float {type:"sin",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.execution_rotation[0]"},0.017453292519943295]}}
data modify storage player_motion: _.transform.cos_yaw set compute default float {type:"cos",input:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.execution_rotation[0]"},0.017453292519943295]}}

# tmp = y*sin(pitch) + z*cos(pitch)
data modify storage player_motion: _.transform.tmp set compute default float {type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.y"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_pitch"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.z"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_pitch"}]}]}

# global.x = x*cos(yaw) - tmp*sin(yaw)
data modify storage player_motion: _.calc.x set compute default float {type:"sub",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.x"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_yaw"}]},right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.transform.tmp"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_yaw"}]}}
# global.y = y*cos(pitch) - z*sin(pitch)
data modify storage player_motion: _.calc.y set compute default float {type:"sub",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.y"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_pitch"}]},right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.z"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_pitch"}]}}
# global.z = x*sin(yaw) + tmp*cos(yaw)
data modify storage player_motion: _.calc.z set compute default float {type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.in.x"},{type:"storage",storage:"player_motion:",path:"_.transform.sin_yaw"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.transform.tmp"},{type:"storage",storage:"player_motion:",path:"_.transform.cos_yaw"}]}]}
