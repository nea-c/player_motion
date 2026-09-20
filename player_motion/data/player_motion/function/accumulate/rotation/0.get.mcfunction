# Relative zero rotation writes the command context rotation onto the marker.
rotate @s ~ ~
data modify storage player_motion: _.rotation set from entity @s Rotation
