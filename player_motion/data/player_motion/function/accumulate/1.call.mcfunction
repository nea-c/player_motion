# Reject player states for which vanilla cannot apply the requested impulse.
execute if entity @s[type=player,gamemode=spectator] run return fail
execute if entity @s[type=player,gamemode=creative] if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_flying:true,is_fall_flying:false}}} run return fail

# A mounted call is either rejected or recursively redirected to the root vehicle.
execute if data storage player_motion: _.in{is_vehicle_execution:false} on vehicle run return fail
execute if data storage player_motion: _.in{is_vehicle_execution:true} on vehicle run return run function player_motion:accumulate/1.call

# Match ImpulseMotion's resistance order when both flags are enabled.
execute if data storage player_motion: _.in{is_explosion:true} run function player_motion:accumulate/2.explosion
execute if data storage player_motion: _.in{is_knockback:true} run function player_motion:accumulate/2.knockback

# Resolve the input vector against the rotation captured at the public call site.
execute if data storage player_motion: _.in{is_looking:true} run function player_motion:accumulate/3.looking
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.x set from storage player_motion: _.in.x
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.y set from storage player_motion: _.in.y
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.z set from storage player_motion: _.in.z

function player_motion:accumulate/4.motion_set
function player_motion:accumulate/5.score
