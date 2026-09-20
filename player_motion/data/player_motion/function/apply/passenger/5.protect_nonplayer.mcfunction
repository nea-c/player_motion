# Passenger protection must not contribute clipped rider motion to the root vector.
# Check original invulnerability once, then reuse the cached storage result.
data modify storage player_motion: _.Invulnerable set value true
execute if predicate {type:"entity_properties",entity:"this",predicate:{nbt:{Invulnerable:true}}} run return fail
execute store success storage player_motion: _.Invulnerable byte 1 run data modify entity @s Invulnerable set value 1b
execute if data storage player_motion: _{Invulnerable:true} run tag @s add player_motion.restore_invulnerable
execute unless data storage player_motion: _{Invulnerable:true} run scoreboard players set #player_motion.passenger_failed PlayerMotion.X 1
