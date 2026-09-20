# Normalize one public API invocation without modifying the caller-owned input.
data modify storage player_motion: _ set value {in:{x:0.0,y:0.0,z:0.0,is_looking:false,is_vehicle_execution:false,is_knockback:false,is_explosion:false,multiplier:{elytra:0.5,swim:0.5,in_water:1.5}}}
data modify storage player_motion: _.in merge from storage player_motion: in

# Capture the call site's rotation before process may change @s to a vehicle.
execute unless data storage neac: {DimensionGenerated:1b} run return fail
function player_motion:accumulate/rotation/1.execution
function player_motion:accumulate/1.call
