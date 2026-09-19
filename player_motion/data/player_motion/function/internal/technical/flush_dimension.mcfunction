# Launch every pending target in this anchor's dimension, then unconditionally
# clear its queue state. A return inside launch/main cannot skip the next pass.
execute as @e[tag=player_motion.pending] at @s run function player_motion:internal/launch/main
execute as @e[tag=player_motion.pending] at @s run function player_motion:internal/launch/cleanup

# Protection restoration is independent of whether an entity has new motion.
execute as @e[type=!minecraft:player,tag=player_motion.restore_invulnerable] run function player_motion:internal/launch/restore_invulnerable
