# Check resistance before changing player modes or reloading root/rider entity NBT.
execute store success score # PlayerMotion.X run attribute @s explosion_knockback_resistance get
execute if score # PlayerMotion.X matches 1 run function player_motion:apply/passenger/1.resistance
execute on passengers run function player_motion:apply/passenger/0.prepare_tree
