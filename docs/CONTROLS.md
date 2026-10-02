# Mouse-first controls

Original defaults informed by documented classic control patterns. They are not a promise of exact modern Conquer Online bindings.

- Left-click terrain: destination movement; left-click a foe: approach and repeated basic cut. Selection uses the visible character footprint, not only its feet
- Left-click Suri or a ground drop: approach and interact
- Ctrl + left-click terrain: directional vault
- Right-click target/ground: cast the currently selected skill
- F1–F10: choose the slot's skill or immediately use its item/interact action. Defaults: Reed Cut, Jade Arc, Threadstrike, Sky Vault, Flask, Gather, then four empty slots
- Tab: live gear portrait and inventory; click/right-click a slot or C/V/B to cycle owned armor/head/weapon
- E: nearby interaction; Space: cursor-directed vault
- F11: realm, local save/load and Controls & Hotbar; F12: guide; Esc: close overlay or open realm menu
- WASD: optional camera-relative secondary movement; mouse wheel: zoom

Controls & Hotbar allows single physical-key remapping, conflict swapping, per-slot action cycling, restore defaults and disabling keyboard movement. Mouse/modifier bindings remain fixed for this prototype. Settings are saved locally in `user://jadebound-controls.cfg`. UI panels consume clicks, and gear buttons do not capture Tab keyboard focus.

The server independently rejects locked skills/gear regardless of hotbar selection or client UI. Profile/mastery values are not accepted in action/equipment messages.

In the live equipment panel, left-click a slot to cycle owned gear and right-click to remove its item. Removed items remain owned. Armor/head/weapon are live; boots/gloves belong to the separate new art study until integration.
