# Transfer the current command rotation to the fixed marker in the isolated dimension.
execute in neac: as 1604-1604-1604-1604-1604 run function player_motion:accumulate/rotation/0.get
data modify storage player_motion: _.execution_rotation set from storage player_motion: _.rotation
