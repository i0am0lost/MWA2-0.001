# MWA2 — a multi-world ("Jail") system for Artificial Academy 2 / AAUnlimited

Tooling for a second, **coupled world** ("Jail") next to the normal school class in AA2 — and, more
generally, a framework for **multiple pre-loaded game worlds** with **instant switching**, an
**interaction-triggered character transfer** between them, and a **persistent memory layer (SSOT/DB)**
that remembers each character's developed state and relationships across worlds (Sims-style: a
relationship survives even while the other character is "away" in another world).

> This repo contains **project tooling only** (mods, a Python orchestrator, the DB, docs) — **not** the
> ~21 GB game installs or saves (see `.gitignore`). Paths are derived at runtime, so it's portable.

## Where it stands (late 2026-06-24)
**Foundation (done, proven live):**
- Instant switch between two pre-loaded worlds (patched multi-client PPeX server, AA2 single-instance
  mutex bypass, inactive world hidden + process-suspended → no sound/CPU, instant resume).
- One entry point (`run_orchestrator.bat`): starts the server + both worlds, world label + in-game
  switch button, save-coupling (each school save ↔ its own jail twin), robust shutdown.
- Reverse-engineered the load path: there is **no callable cold-loader** → the only crash-free load is
  the game's own menu-load, automated once at boot (RE notes in `_re/RE_LADEFUNKTION.md`).

**Transfer school → jail (the hard part — working):**
- Dominance combo (`INSULT → FIGHT → FORCE_H`) enslaves a target. Transfer is **commit-on-save**:
  saving in school commits it to a per-day journal; the orchestrator derives jail's roster from it.
- A char materializes in jail via **KickCard** (remove from school) + **AddCard** (add to jail) — both
  proven live. Its **developed self-values** (virtue/intelligence/strength/sociability) are injected.
- **Relationship memory**: a full relationship graph is snapshotted continuously into the SSOT
  (`char_rels`), so relationships are remembered before any transfer and reactivated when both chars
  are co-present again. Confirmed building live.
- **Module catalog**: all 466 AAU modules scanned to `module_catalog.json` (name + description).

**Next:** a card **module editor** (the AAU module list lives in a clean `aaUd` PNG chunk — feasibility
confirmed) driven by a state→module map (e.g. corrupted → "Sex Addict"); a return path (jail → school);
jail world mechanics (reactive node-blocking → progressive dungeon; night-only phase; reskin); an RPG
layer (activity DB, status modules, loneliness from social wealth).

**Hard engine limits (worked around, not removed):** 25-character roster cap, no new map geometry, no
new action verbs, no callable cold-loader (menu automation), live-reload crashes (kill+restart),
module list not writable from Lua at runtime (→ external card edit at the day boundary).

## Components
- `orchestrator.py` — runtime orchestrator (stdlib + ctypes only): server, worlds, switch, coupling,
  the SSOT transfer pipeline (commit-on-save → day-keyed journal → derive-on-load).
- `playthrough_db.py` — per-playthrough SQLite long-term memory: `transfers`, `char_rels`, `world_state`.
- `module_scan.py` → `module_catalog.json`/`.md` — catalog of all AAU modules.
- **Custom Lua mods** (in `school|jail/AAUnlimited/mod/`): `master_slave` (combo → slave), `jail_intake`
  (rebuild jail roster from the SSOT: KickCard + AddCard + value/relationship injection), `rel_snapshot`
  (continuous relationship memory), `logperiod` (day/phase flag), `orch_savename` (save-name flag).

## Detailed working docs (currently German)
The deep design/state/RE notes are in German — ping me if you want them translated:
- `AA2_Jail_Projekt_Notizen.md` — design doc; **STATUS section at the top** = overview (done / in progress / planned).
- `HANDOVER_transfer_2026-06-24.md` — current build state in detail.
- `HANDOVER_*` / `_re/RE_LADEFUNKTION.md` — coupling, combo trigger, reverse engineering.

## Run (local, Windows)
`run_orchestrator.bat` (as admin). Needs Python 3.12 and an existing AA2/AAUnlimited install placed as
`school/` and `jail/` siblings of these files.
