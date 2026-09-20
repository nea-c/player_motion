#> player_motion:internal/technical/tick
schedule function player_motion:internal/technical/tick 1t replace

# A global player selector supplies one execution anchor per loaded player
# dimension. The helper completes cleanup before another anchor can retry it.
execute as @a at @s run function player_motion:internal/technical/flush_dimension
