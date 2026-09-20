# Convert this call to six-decimal fixed point after clamping each float component.
execute store result score #delta PlayerMotion.X run compute default float {type:"minecraft:round",input:{type:"minecraft:mul",inputs:[{type:"minecraft:min",inputs:[{type:"minecraft:max",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.calc.x"},-1024.0]},1024.0]},1000000.0]}}
execute store result score #delta PlayerMotion.Y run compute default float {type:"minecraft:round",input:{type:"minecraft:mul",inputs:[{type:"minecraft:min",inputs:[{type:"minecraft:max",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.calc.y"},-1024.0]},1024.0]},1000000.0]}}
execute store result score #delta PlayerMotion.Z run compute default float {type:"minecraft:round",input:{type:"minecraft:mul",inputs:[{type:"minecraft:min",inputs:[{type:"minecraft:max",inputs:[{type:"minecraft:storage",storage:"player_motion:",path:"_.calc.z"},-1024.0]},1024.0]},1000000.0]}}

# Add safe operands, then immediately saturate every accumulated component.
scoreboard players operation @s PlayerMotion.X += #delta PlayerMotion.X
execute if score @s PlayerMotion.X matches 1024000001.. run scoreboard players set @s PlayerMotion.X 1024000000
execute if score @s PlayerMotion.X matches ..-1024000001 run scoreboard players set @s PlayerMotion.X -1024000000
scoreboard players operation @s PlayerMotion.Y += #delta PlayerMotion.Y
execute if score @s PlayerMotion.Y matches 1024000001.. run scoreboard players set @s PlayerMotion.Y 1024000000
execute if score @s PlayerMotion.Y matches ..-1024000001 run scoreboard players set @s PlayerMotion.Y -1024000000
scoreboard players operation @s PlayerMotion.Z += #delta PlayerMotion.Z
execute if score @s PlayerMotion.Z matches 1024000001.. run scoreboard players set @s PlayerMotion.Z 1024000000
execute if score @s PlayerMotion.Z matches ..-1024000001 run scoreboard players set @s PlayerMotion.Z -1024000000

# Queue only after all three accumulated scores are valid.
tag @s add player_motion.pending
