# Recheck magnitude after protection's clipped-motion correction, which can
# cancel the requested impulse even though the input scores were nonzero.
data modify storage player_motion: _.launch.horizontal set compute default float {type:"sqrt",input:{type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.x"},{type:"storage",storage:"player_motion:",path:"_.launch.x"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.z"},{type:"storage",storage:"player_motion:",path:"_.launch.z"}]}]}}
data modify storage player_motion: _.launch.magnitude set compute default float {type:"sqrt",input:{type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.horizontal"},{type:"storage",storage:"player_motion:",path:"_.launch.horizontal"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.y"},{type:"storage",storage:"player_motion:",path:"_.launch.y"}]}]}}
execute store result score # PlayerMotion.X run compute default float {type:"ceil",input:{type:"min",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.magnitude"},1.0]}}
execute if score # PlayerMotion.X matches 0 run return 0
data modify storage player_motion: _.launch.full_count set compute default float {type:"floor",input:{type:"div",left:{type:"storage",storage:"player_motion:",path:"_.launch.magnitude"},right:0.8}}
execute store result score # PlayerMotion.X run data get storage player_motion: _.launch.full_count
data modify storage player_motion: _.launch.residual set compute default float {type:"min",inputs:[{type:"max",inputs:[{type:"sub",left:{type:"storage",storage:"player_motion:",path:"_.launch.magnitude"},right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.full_count"},0.8]}},0.0]},0.8]}
execute store result score # PlayerMotion.Y run compute default float {type:"ceil",input:{type:"storage",storage:"player_motion:",path:"_.launch.residual"}}
data modify storage player_motion: _.launch.unit_y set compute default float {type:"div",left:{type:"storage",storage:"player_motion:",path:"_.launch.y"},right:{type:"storage",storage:"player_motion:",path:"_.launch.magnitude"}}
data modify storage player_motion: _.launch.unit_horizontal set compute default float {type:"div",left:{type:"storage",storage:"player_motion:",path:"_.launch.horizontal"},right:{type:"storage",storage:"player_motion:",path:"_.launch.magnitude"}}

# Preserve the former pose-based eye-height geometry without lookup tables.
data modify storage player_motion: _.launch.eye_height set value 1.62f
execute anchored eyes positioned ^ ^ ^ if entity @s[distance=..1.27] run data modify storage player_motion: _.launch.eye_height set value 1.27f
execute anchored eyes positioned ^ ^ ^ if entity @s[distance=..0.41] run data modify storage player_motion: _.launch.eye_height set value 0.4f

# full_distance = (1 - 0.8) * 12, strictly positive.
data modify storage player_motion: _.launch.full_distance set compute default float {type:"mul",inputs:[{type:"sub",left:1.0,right:0.8},12.0]}
data modify storage player_motion: _.launch.full_q set compute default float {type:"min",inputs:[{type:"max",inputs:[{type:"div",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.unit_horizontal"},{type:"storage",storage:"player_motion:",path:"_.launch.eye_height"}]},right:{type:"storage",storage:"player_motion:",path:"_.launch.full_distance"}},-1.0]},1.0]}
data modify storage player_motion: _.launch.full_d set compute default float {type:"negate",input:{type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.eye_height"},{type:"storage",storage:"player_motion:",path:"_.launch.unit_y"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.full_distance"},{type:"sqrt",input:{type:"max",inputs:[{type:"sub",left:1.0,right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.full_q"},{type:"storage",storage:"player_motion:",path:"_.launch.full_q"}]}},0.0]}}]}]}}

# Skip residual geometry and the residual crystal entirely at exact multiples.
# Residual is clamped to [0, 0.8], so its falloff distance is at least 2.4.
data modify storage player_motion: _.launch.d set value 0.0f
execute if score # PlayerMotion.Y matches 1 run data modify storage player_motion: _.launch.distance set compute default float {type:"mul",inputs:[{type:"sub",left:1.0,right:{type:"storage",storage:"player_motion:",path:"_.launch.residual"}},12.0]}
execute if score # PlayerMotion.Y matches 1 run data modify storage player_motion: _.launch.q set compute default float {type:"min",inputs:[{type:"max",inputs:[{type:"div",left:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.unit_horizontal"},{type:"storage",storage:"player_motion:",path:"_.launch.eye_height"}]},right:{type:"storage",storage:"player_motion:",path:"_.launch.distance"}},-1.0]},1.0]}
execute if score # PlayerMotion.Y matches 1 run data modify storage player_motion: _.launch.d set compute default float {type:"negate",input:{type:"add",inputs:[{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.eye_height"},{type:"storage",storage:"player_motion:",path:"_.launch.unit_y"}]},{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.distance"},{type:"sqrt",input:{type:"max",inputs:[{type:"sub",left:1.0,right:{type:"mul",inputs:[{type:"storage",storage:"player_motion:",path:"_.launch.q"},{type:"storage",storage:"player_motion:",path:"_.launch.q"}]}},0.0]}}]}]}}
