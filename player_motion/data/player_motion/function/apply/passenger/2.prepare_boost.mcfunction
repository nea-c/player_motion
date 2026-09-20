# Aim at 2 before clamping to provide margin for the float provider's rounding.
execute store result storage player_motion: _.passenger.resistance float 0.000000001 run scoreboard players get # PlayerMotion.X
data modify storage player_motion: _.passenger.boost set compute default float {type:"sub",left:{type:"div",left:2.0,right:{type:"storage",storage:"player_motion:",path:"_.passenger.resistance"}},right:1.0}
function player_motion:apply/passenger/3.boost with storage player_motion: _.passenger
