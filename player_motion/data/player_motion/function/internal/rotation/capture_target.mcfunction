# Override the command rotation with the final target's rotation before using the marker.
execute rotated as @s in neac: as 1604-1604-1604-1604-1604 run function player_motion:internal/rotation/get
data modify storage player_motion: _.target_rotation set from storage player_motion: _.rotation
