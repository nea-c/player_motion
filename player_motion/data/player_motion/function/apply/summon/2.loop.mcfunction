scoreboard players remove #player_motion PlayerMotion.X 1
execute summon end_crystal run damage @s 0
execute if score #player_motion PlayerMotion.X matches 1.. run function player_motion:apply/summon/2.loop
