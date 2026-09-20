#> player_motion:load


scoreboard objectives add PlayerMotion.X dummy
scoreboard objectives add PlayerMotion.Y dummy
scoreboard objectives add PlayerMotion.Z dummy

schedule function player_motion:schedule_tick 1t replace
