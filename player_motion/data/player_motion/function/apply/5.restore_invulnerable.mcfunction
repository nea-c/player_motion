# Call after launch and retry each tick for tagged entities in every dimension.
# Never rewrite players or targets whose original invulnerability we did not change.
execute if entity @s[type=player] run return fail
execute unless entity @s[tag=player_motion.restore_invulnerable] run return fail

# Entity.load preserves Motion only within inclusive +/-10. Two exact double
# floor probes avoid float rounding at the boundary; unsafe targets keep the tag.
data modify storage player_motion: _.Motion set from entity @s Motion
execute if predicate {type:"any_of",terms:[\
  {type:"inverted",term:{type:"float_value_check",value:{type:"storage",storage:"player_motion:",path:"_.Motion[0]"},test:{min:-10,max:10}}},\
  {type:"inverted",term:{type:"float_value_check",value:{type:"storage",storage:"player_motion:",path:"_.Motion[1]"},test:{min:-10,max:10}}},\
  {type:"inverted",term:{type:"float_value_check",value:{type:"storage",storage:"player_motion:",path:"_.Motion[2]"},test:{min:-10,max:10}}},\
]} run return fail

data modify entity @s Invulnerable set value 0b
tag @s remove player_motion.restore_invulnerable
