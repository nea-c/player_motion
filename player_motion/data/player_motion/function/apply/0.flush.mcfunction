# Launch every pending target in this anchor's dimension, then unconditionally
# clear its queue state. A return inside launch/main cannot skip the next pass.
# An unbounded @e is global; distance limits the queries to this dimension.
execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/1.launch
execute as @e[tag=player_motion.pending,distance=0..] at @s run function player_motion:apply/6.cleanup

# Protection restoration is independent of whether an entity has new motion.
execute as @e[type=!player,tag=player_motion.restore_invulnerable,distance=0..] run function player_motion:apply/5.restore_invulnerable
