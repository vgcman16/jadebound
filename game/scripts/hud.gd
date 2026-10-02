class_name JadeHUD
extends Control
var state:Dictionary={}
var local_id:int=1
var mode:String="offline"
var inventory:bool=false
var help:bool=false
var font:Font=ThemeDB.fallback_font
var notice:String=""
var demo:bool=false
const INK=Color("132c2e")
const PAPER=Color("ede6cb")
const GOLD=Color("e4bf76")
const JADE=Color("70d9ba")
func _ready():
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func panel(rect:Rect2,color:Color=Color("132c2eee")):
	draw_style_box(style(color),rect)
func style(color:Color)->StyleBoxFlat:
	var s=StyleBoxFlat.new()
	s.bg_color=color
	s.border_color=Color("67776a")
	s.set_border_width_all(1)
	s.set_corner_radius_all(4)
	return s
func text(value:String,pos:Vector2,size:int=18,color:Color=PAPER):
	draw_string(font,pos,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)
func line(a:Vector2,b:Vector2,color:Color=Color("597469")):
	draw_line(a,b,color,1)
func _draw():
	var w=size.x
	var h=size.y
	var p:Dictionary=state.get("players",{}).get(local_id,{})
	panel(Rect2(24,24,306,120))
	text("JADEBOUND",Vector2(43,57),29,GOLD)
	text("ASHES OF LANTERN VALE",Vector2(45,78),12,Color("9dbab0"))
	if not p.is_empty():
		text("WANDERER  /  LV. %02d"%p.level,Vector2(45,105),15)
		text("%s  ·  %d copper"%["DAWNSTEEL" if p.upgraded else "REEDBLADE",p.gold],Vector2(45,128),12,JADE)
	panel(Rect2(w-268,24,244,220))
	text("LANTERN VALE",Vector2(w-250,52),16,GOLD)
	text("Jade Coast · dawn",Vector2(w-250,72),12,Color("a9bdb1"))
	var map=Rect2(w-249,85,205,138)
	draw_rect(map,Color("324c44"))
	for i in 6:
		line(Vector2(map.position.x+i*41,map.position.y),Vector2(map.position.x+i*41,map.end.y),Color("40584b"))
	for i in 4:
		line(Vector2(map.position.x,map.position.y+i*46),Vector2(map.end.x,map.position.y+i*46),Color("40584b"))
	var transform_pos=func(pos:Vector2):return map.position+Vector2((pos.x+20)/40*map.size.x,(pos.y+20)/40*map.size.y)
	draw_circle(transform_pos.call(JadeWorld.ELDER),4,GOLD)
	for e in state.get("enemies",{}).values():
		if e.dead<=0: draw_circle(transform_pos.call(e.pos),2.7,Color("d88067"))
	for player in state.get("players",{}).values(): draw_circle(transform_pos.call(player.pos),4,JADE)
	panel(Rect2(w-332,266,308,147))
	text("THE LAST LANTERNS",Vector2(w-314,296),17,GOLD)
	if not p.is_empty():
		if p.quest==0:
			text("Find Keeper Suri in the village",Vector2(w-314,326),15)
			text("Approach and press E",Vector2(w-314,351),14,JADE)
		elif p.quest==1:
			text("Recover ember seals",Vector2(w-314,326),15)
			text("%d / 5  gathered"%p.seals,Vector2(w-314,351),19,JADE)
			text("Return to Suri for Dawnsteel",Vector2(w-314,382),13)
		else:
			text("Lantern Vale is safe",Vector2(w-314,329),17,JADE)
			text("Dawnsteel blade earned",Vector2(w-314,357),14)
	var bar_w=560.0
	var x=(w-bar_w)/2
	panel(Rect2(x-22,h-139,bar_w+44,118))
	if not p.is_empty():
		draw_rect(Rect2(x,h-126,270,9),Color("463e39"))
		draw_rect(Rect2(x,h-126,270*float(p.hp)/p.max_hp,9),Color("d87968"))
		draw_rect(Rect2(x+290,h-126,270,9),Color("304845"))
		draw_rect(Rect2(x+290,h-126,270*p.stamina/100,9),JADE)
		text("VITALITY  %d / %d"%[p.hp,p.max_hp],Vector2(x,h-102),12)
		text("QI  %d / 100"%p.stamina,Vector2(x+290,h-102),12)
	var keys=["LMB / 1","Q","R","SPACE","H","E"]
	var labels=["Slash","Jade arc","Threadstrike","Sky vault","Flask","Gather"]
	for i in 6:
		var rect=Rect2(x+i*95,h-89,84,51)
		panel(rect,Color("284a46"))
		text(keys[i],rect.position+Vector2(8,18),12,GOLD)
		text(labels[i],rect.position+Vector2(8,39),12)
		if not p.is_empty():
			var cd=p.arc_cd if i==1 else (p.line_cd if i==2 else 0)
			if cd>0:text("%.1f"%cd,rect.position+Vector2(55,18),13,JADE)
	text("WASD / click to move  ·  TAB satchel  ·  F1 realm  ·  F2 guide",Vector2(x+47,h-8),12,Color("b2c3b8"))
	panel(Rect2(24,h-137,285,113))
	text("%s REALM"%mode.to_upper(),Vector2(41,h-111),13,JADE)
	text("%d wanderer%s"%[state.get("players",{}).size(),"" if state.get("players",{}).size()==1 else "s"],Vector2(41,h-87),15)
	text("Original playable prototype · v0.1",Vector2(41,h-58),12,Color("b0bfb1"))
	if demo: text("ENGINE GAMEPLAY CAPTURE",Vector2(41,h-37),11,GOLD)
	if not p.is_empty():
		var message=notice if not notice.is_empty() else p.notice
		var bounds=Rect2(x-125,h-226,810,66)
		panel(bounds,Color("1b3335e6"))
		# Bounded hand wrapping without texture-rich rich text overlays.
		var lines=wrap_lines(message,90)
		for i in mini(lines.size(),3):text(lines[i],bounds.position+Vector2(18,24+i*19),14,GOLD)
		if p.dead>0:
			panel(Rect2(w/2-200,h/2-60,400,105),Color("1a2428ed"))
			text("THE SHRINE CALLS YOU HOME",Vector2(w/2-169,h/2-20),20,GOLD)
			text("Return in %.1f seconds"%p.dead,Vector2(w/2-94,h/2+13),16)
	if inventory and not p.is_empty():
		panel(Rect2(24,170,315,309))
		text("THE WANDERER'S SATCHEL",Vector2(43,202),19,GOLD)
		text("Blade: %s"%("Dawnsteel +6" if p.upgraded else "Reedblade"),Vector2(43,245),17,JADE)
		text("Cloudleaf flasks     %d"%p.potions,Vector2(43,284),17)
		text("Ember seals           %d"%p.seals,Vector2(43,320),17)
		text("Copper                    %d"%p.gold,Vector2(43,356),17)
		text("Attunement XP        %d / %d"%[p.xp,p.level*80],Vector2(43,394),16)
		text("Press H to drink · TAB to close",Vector2(43,454),13,Color("afc6b8"))
	if help:
		panel(Rect2(w/2-265,170,530,390))
		text("A WANDERER'S GUIDE",Vector2(w/2-240,210),24,GOLD)
		var lines=["WASD moves relative to the camera. Click ground to walk.","Click a marauder to approach and attack automatically.","Q: Jade arc hits all nearby enemies. Costs 32 qi.","R: Threadstrike hits a thin aimed line. Costs 25 qi.","Space or Ctrl+click: vault toward cursor. Costs 22 qi.","E: talk to Suri / collect nearby gold and ember seals.","H: drink a healing flask. Suri also restores vitality.","Gather five seals, return to Suri, earn Dawnsteel.","F1: local / LAN realm. No public servers or accounts yet.","F2 closes this guide. Escape quits the game."]
		for i in lines.size():text(lines[i],Vector2(w/2-240,246+i*28),14)

func wrap_lines(value:String,limit:int)->Array[String]:
	var result:Array[String]=[]
	var current=""
	for word in value.split(" "):
		if (current+word).length()>limit:
			result.append(current)
			current=""
		current+=word+" "
	if not current.is_empty():result.append(current)
	return result
