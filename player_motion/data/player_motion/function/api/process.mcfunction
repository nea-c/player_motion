# Reject player states for which vanilla cannot apply the requested impulse.
execute if entity @s[type=player,gamemode=spectator] run return fail
execute if entity @s[type=player,gamemode=creative] if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_flying:true,is_fall_flying:false}}} run return fail

# A mounted call is either rejected or recursively redirected to the root vehicle.
execute if data storage player_motion: _.in{is_vehicle_execution:false} on vehicle run return fail
execute if data storage player_motion: _.in{is_vehicle_execution:true} on vehicle run return run function player_motion:api/process

# Resolve the input vector against the rotation captured at the public call site.
execute if data storage player_motion: _.in{is_looking:true} run function player_motion:api/transform/execution_to_global
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.x set from storage player_motion: _.in.x
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.y set from storage player_motion: _.in.y
execute unless data storage player_motion: _.in{is_looking:true} run data modify storage player_motion: _.calc.z set from storage player_motion: _.in.z

# Preserve the final target rotation for target-local state multipliers in Task 3.
function player_motion:internal/rotation/capture_target

# Match ImpulseMotion's resistance order when both flags are enabled.
execute if data storage player_motion: _.in{is_explosion:true} run function player_motion:api/resistance/explosion
execute if data storage player_motion: _.in{is_knockback:true} run function player_motion:api/resistance/knockback

# Apply target-state multipliers only to this call in target-local coordinates.
function player_motion:api/transform/global_to_target
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_in_water:true}}} run function player_motion:api/multiplier/in_water
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_fall_flying:true}}} run function player_motion:api/multiplier/elytra
execute if predicate {type:"entity_properties",entity:"this",predicate:{flags:{is_swimming:true}}} run function player_motion:api/multiplier/swim
function player_motion:api/transform/target_to_global

# Append the bounded six-decimal delta to this target's queued motion.
function player_motion:api/accumulate
