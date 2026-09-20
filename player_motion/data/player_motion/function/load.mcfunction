#> player_motion:load

data modify storage player_motion: _ set value {}

scoreboard objectives add PlayerMotion.X dummy
scoreboard objectives add PlayerMotion.Y dummy
scoreboard objectives add PlayerMotion.Z dummy

schedule function player_motion:schedule_tick 1t replace
