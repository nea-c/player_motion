# Clear only queue-owned state. Deferred invulnerability restoration has its
# own tag and may need to survive until the entity's motion is safe to reload.
scoreboard players reset @s PlayerMotion.X
scoreboard players reset @s PlayerMotion.Y
scoreboard players reset @s PlayerMotion.Z
tag @s remove player_motion.pending
