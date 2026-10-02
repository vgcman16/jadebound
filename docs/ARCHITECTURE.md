# Jadebound architecture and production boundaries

## Implemented foundation

The same deterministic-step `JadeWorld` model owns movement, combat, cooldowns, qi, health, AI, death/respawn, loot ownership, progression and quest rewards. Offline mode hosts this model locally. A dedicated headless server or host owns it in multiplayer; clients send intentions, never health, reward or inventory changes. `JadeNetwork` steps at 20 Hz and sends authoritative snapshots at 20 Hz over ENet. Visual interpolation is presentation only.

Input rejects non-finite vectors and stale sequence numbers, clamps movement length and map targets. Reliable action requests have a per-peer rate gate and model cooldown/resource validation. Fresh drops are reserved for their killer for 15 seconds, then become collectible by other nearby players. Quest rewards are single-use per session. Sessions are limited to eight players. UI loopback host binds only 127.0.0.1. To expose to a trusted LAN, explicitly launch a server with `--bind=YOUR_LAN_IP`; no automatic UPnP or firewall changes.

## Current limitations

This is a small-session multiplayer foundation, not a live MMO service. No account authentication, encrypted transport, persistent online database, zone transfer, interest management, reconnect recovery, trading, PvP economy, public matchmaking or deployment is included. Snapshots contain whole-zone state. Enemy collision is simple steering and player obstacles use coarse circular bounds, not production pathfinding. Offline JSON saves are intentionally user-editable and must never be imported into a future online realm.

The test suite validates local gameplay rules and, when enabled, loopback connectivity. It does not establish resistance to hostile Internet clients, large-scale performance, WAN latency quality or MMO readiness. Do not expose the prototype to the public Internet.

## Staged MMO route

1. Polish the vertical slice: combat readability, obstacle navigation, sound, wider input/visual QA
2. Authoritative zone server: fixed protocol/version, input budgets, interest sets, snapshot delta compression, client prediction/reconciliation, reconnect tokens, soak tests
3. Accounts and durable state: authenticated sessions, relational character/inventory ownership, atomic reward/item transactions, migrations and backups
4. Multiple zones: handoff service, idempotent transfers, instance lifecycle, persistence recovery and cross-zone tests
5. Trusted closed alpha: measured concurrency/latency targets, telemetry, abuse controls, deployment and incident procedures
6. Only then consider social economy, secure trading, guild territory and production scale

No hosting account, paid service, account secret or runner registration is provisioned by this project.
