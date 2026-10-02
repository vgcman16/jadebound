# Engine decision — 2026-10-02

Pin the already installed **Godot 4.6.3 stable** with **Blender 4.3.2**. Godot 4.7.2 is newer according to the official archive; an upgrade is not required for this bounded prototype. The native renderer, scene graph, GDScript and ENet support provide a practical path to a low-poly isometric game with a dedicated authoritative server. Blender emits original GLB geometry/animations plus editable .blend source.

Official references checked:
- https://godotengine.org/download/archive/
- https://docs.godotengine.org/en/4.6/tutorials/networking/high_level_multiplayer.html
- https://docs.godotengine.org/en/4.6/tutorials/export/exporting_for_linux.html
- https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html

A local multiplayer test demonstrates connectivity and replication, not public deployment or MMO scalability. ENet UDP is native-platform oriented; a future web client needs a different transport (WebSocket/WebRTC).
