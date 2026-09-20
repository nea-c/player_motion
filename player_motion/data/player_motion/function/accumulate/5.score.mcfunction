# Convert this call to six-decimal fixed point after clamping each float component.
execute store result score #player_motion PlayerMotion.X run compute default float {type:"round",input:{type:"mul",inputs:[{type:"min",inputs:[{type:"max",inputs:[{type:"storage",storage:"player_motion:",path:"_.calc.x"},-1024.0]},1024.0]},1000000.0]}}
execute store result score #player_motion PlayerMotion.Y run compute default float {type:"round",input:{type:"mul",inputs:[{type:"min",inputs:[{type:"max",inputs:[{type:"storage",storage:"player_motion:",path:"_.calc.y"},-1024.0]},1024.0]},1000000.0]}}
execute store result score #player_motion PlayerMotion.Z run compute default float {type:"round",input:{type:"mul",inputs:[{type:"min",inputs:[{type:"max",inputs:[{type:"storage",storage:"player_motion:",path:"_.calc.z"},-1024.0]},1024.0]},1000000.0]}}

# Add safe operands, then immediately saturate every accumulated component.
scoreboard players operation @s PlayerMotion.X += #player_motion PlayerMotion.X
execute if score @s PlayerMotion.X matches 1024000001.. run scoreboard players set @s PlayerMotion.X 1024000000
execute if score @s PlayerMotion.X matches ..-1024000001 run scoreboard players set @s PlayerMotion.X -1024000000
scoreboard players operation @s PlayerMotion.Y += #player_motion PlayerMotion.Y
execute if score @s PlayerMotion.Y matches 1024000001.. run scoreboard players set @s PlayerMotion.Y 1024000000
execute if score @s PlayerMotion.Y matches ..-1024000001 run scoreboard players set @s PlayerMotion.Y -1024000000
scoreboard players operation @s PlayerMotion.Z += #player_motion PlayerMotion.Z
execute if score @s PlayerMotion.Z matches 1024000001.. run scoreboard players set @s PlayerMotion.Z 1024000000
execute if score @s PlayerMotion.Z matches ..-1024000001 run scoreboard players set @s PlayerMotion.Z -1024000000

# Release call-local scratch scores before queueing the target.
scoreboard players reset #player_motion

# Queue only after all three accumulated scores are valid.
tag @s add player_motion.pending
