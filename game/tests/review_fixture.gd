extends RefCounted
## Local automated visual review only. Never run for a connected player or RPC.
static func qualify(model):
	var p=model.players[1]
	p.level=6
	p.practice={"saber":24,"polearm":24}
	p.mastery.slash=8
	p.mastery.jade_arc=3
	model.sync_progression(p)
	# The dependent mastery unlock is evaluated after Jade Arc has been learned.
	model.sync_progression(p)
	model.recalculate_stats(p)
	p.hp=p.max_hp
