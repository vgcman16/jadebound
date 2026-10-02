class_name JadeNetwork
extends Node
## Server owns simulation and validates input. Only intent crosses client -> server.
signal state_received(state:Dictionary)
signal effects_received(effects:Array)
signal connection_note(note:String)
const PORT=27841
var model:JadeWorld
var state:Dictionary={}
var mode:String="offline"
var local_id:int=1
var sequence:int=0
var accumulator:float=0
var snap_timer:float=0
var commands:Dictionary={}
var dedicated:bool=false
var snapshot_count:int=0
var max_seen_players:int=0
var max_snapshot_bytes:int=0

func _ready():
	multiplayer.peer_connected.connect(_peer_connected)
	multiplayer.peer_disconnected.connect(_peer_disconnected)
	multiplayer.connected_to_server.connect(_connected)
	multiplayer.connection_failed.connect(func(): connection_note.emit("Connection failed. Check host and UDP port 27841."))
	multiplayer.server_disconnected.connect(func(): connection_note.emit("Host disconnected. Open the realm menu to start a new offline session."))
	start_offline()

func start_offline():
	multiplayer.multiplayer_peer=OfflineMultiplayerPeer.new()
	mode="offline"
	local_id=1
	model=JadeWorld.new()
	model.add_player(1)
	state=model.snapshot()
	sequence=0

func host(bind_address:String="127.0.0.1",server_only:bool=false)->Error:
	var peer=ENetMultiplayerPeer.new()
	peer.set_bind_ip(bind_address)
	var err=peer.create_server(PORT,JadeWorld.MAX_PLAYERS)
	if err!=OK: return err
	multiplayer.multiplayer_peer=peer
	mode="server" if server_only else "host"
	dedicated=server_only
	local_id=1
	sequence=0
	model=JadeWorld.new()
	if not dedicated: model.add_player(1,"Host Wanderer")
	state=model.snapshot()
	connection_note.emit("Hosting %s · UDP %d"%[bind_address,PORT])
	return OK

func join(address:String)->Error:
	var peer=ENetMultiplayerPeer.new()
	var err=peer.create_client(address,PORT)
	if err!=OK: return err
	multiplayer.multiplayer_peer=peer
	mode="client"
	model=null
	state={}
	sequence=0
	connection_note.emit("Connecting to %s…"%address)
	return OK

func _connected():
	local_id=multiplayer.get_unique_id()
	connection_note.emit("Connected · authoritative realm")

func _peer_connected(id:int):
	if mode in ["host","server"]:
		model.add_player(id,"Wanderer %d"%(id%1000))
		print("JADE_PEER_JOINED ",id)

func _peer_disconnected(id:int):
	if model:
		model.players.erase(id)
		commands.erase(id)
		commands.erase(str(id)+":equip")

func send_input(move:Vector2,target:Vector2,use_target:bool):
	sequence+=1
	if mode=="client":
		if multiplayer.multiplayer_peer.get_connection_status()==MultiplayerPeer.CONNECTION_CONNECTED:
			submit_input.rpc_id(1,sequence,move,target,use_target)
	elif model: model.input(local_id,sequence,move,target,use_target)

func send_action(kind:int,aim:Vector2):
	if mode=="client":
		if multiplayer.multiplayer_peer.get_connection_status()==MultiplayerPeer.CONNECTION_CONNECTED: submit_action.rpc_id(1,kind,aim)
	elif model: model.action(local_id,kind,aim)

func send_equip(slot:String,item_id:String):
	if mode=="client":
		if multiplayer.multiplayer_peer.get_connection_status()==MultiplayerPeer.CONNECTION_CONNECTED:submit_equip.rpc_id(1,slot,item_id)
	elif model:model.equip(local_id,slot,item_id)

@rpc("any_peer","call_remote","reliable",1)
func submit_equip(slot:String,item_id:String):
	if not mode in ["server","host"]:return
	if slot.length()>16 or item_id.length()>48:return
	var sender=multiplayer.get_remote_sender_id()
	var key=str(sender)+":equip"
	var now=Time.get_ticks_msec()
	if now-int(commands.get(key,0))<100:return
	commands[key]=now
	model.equip(sender,slot,item_id)

@rpc("any_peer","call_remote","unreliable_ordered",0)
func submit_input(seq:int,move:Vector2,target:Vector2,use_target:bool):
	if not mode in ["server","host"]: return
	var sender=multiplayer.get_remote_sender_id()
	model.input(sender,seq,move,target,use_target)

@rpc("any_peer","call_remote","reliable",1)
func submit_action(kind:int,aim:Vector2):
	if not mode in ["server","host"]: return
	var sender=multiplayer.get_remote_sender_id()
	var now=Time.get_ticks_msec()
	# Per-peer rate gate bounds action processing independently of cooldowns.
	if now-int(commands.get(sender,0))<70: return
	commands[sender]=now
	model.action(sender,kind,aim)

@rpc("authority","call_remote","unreliable_ordered",0)
func receive_state(payload:PackedByteArray):
	if payload.size()>65536:return
	var raw=payload.decompress_dynamic(262144,FileAccess.COMPRESSION_DEFLATE)
	if raw.is_empty():return
	var decoded=bytes_to_var(raw)
	if not decoded is Dictionary:return
	state=decoded
	max_seen_players=maxi(max_seen_players,state.get("players",{}).size())
	snapshot_count+=1
	state_received.emit(state)

@rpc("authority","call_remote","reliable",1)
func receive_effects(payload:Array):
	effects_received.emit(payload)

func _physics_process(delta:float):
	if not model: return
	accumulator+=minf(delta,0.1)
	while accumulator>=0.05:
		model.tick(0.05)
		accumulator-=0.05
	snap_timer+=delta
	if snap_timer>=0.05:
		snap_timer-=0.05
		state=model.snapshot()
		state_received.emit(state)
		if mode in ["host","server"] and not multiplayer.get_peers().is_empty():
			var packet=var_to_bytes(state).compress(FileAccess.COMPRESSION_DEFLATE)
			max_snapshot_bytes=maxi(max_snapshot_bytes,packet.size())
			receive_state.rpc(packet)
		if not model.events.is_empty():
			effects_received.emit(model.events)
			if mode in ["host","server"] and not multiplayer.get_peers().is_empty(): receive_effects.rpc(model.events)
			model.events.clear()
