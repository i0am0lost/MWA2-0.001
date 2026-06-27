# MWA2 — a multi-world ("Jail") system for Artificial Academy 2 / AAUnlimited

Tooling for a second, **coupled world** ("Jail") next to the normal school class in AA2 — and, more
generally, a framework for **multiple pre-loaded game worlds** with **instant switching**, an
**interaction-triggered character transfer** between them, and a **persistent memory layer (SSOT/DB)**
that remembers each character's developed state and relationships across worlds (Sims-style: a
relationship survives even while the other character is "away" in another world).

> **This repo is the SOURCE** (mods, the Python layer, docs, catalogs). The **runnable package**
> (`MWA2_V0.x/`) additionally ships the two game worlds, a bundled Python, and the patched PPeX server —
> those are excluded from git (see `.gitignore`) and distributed as a copy-and-run folder. Everything
> resolves at runtime relative to the package, so it's fully portable.

## What this really is — and why it replicates
This isn't "a jail mod". It's a **generic multi-world extension** for AA2. **"Jail" is just the first
instance.** The expensive part is built **once**: the engine workarounds (two pre-loaded instances, instant
switch via window-hide + process-suspend, the patched multi-client PPeX server, the single-instance-mutex
bypass, the menu-load path), plus the **interaction-triggered transfer** and the **SSOT memory layer**.

After that, **each additional world (Resort, Beach, Apartment, …) is mostly a config entry + a reskin** —
*"worlds as config, not hardcoded"*. And the payoff is **emergent, not hand-coded**: a character develops
differently in different worlds, and AA2's own compatibility engine turns the divergence into friction/drama
**by itself** — you only have to transfer the diverged state correctly (the SSOT does that).

## Core principle: cards are never modified; the SSOT is the brain
Character cards are **pristine, shareable base data** — we **never write to them** (a single changed bit
breaks the card for someone without our mod). **All of our state lives externally in the SSOT** (one
`memory.db` per playthrough). At runtime:

- **Identity** is a stable, rename-proof id linked to the **base card** (not the name, never the seat). The
  active roster is rebuilt from the SSOT, so the same base card can be a *different* evolved character in
  different playthroughs; a character that leaves the roster keeps its data "on ice" and gets it back on return.
- **Modules are injected in-memory at load** by a runtime hook on AAU's own `AAUCardData::UpdateModules`
  (the card file is untouched). The hook reads each card's module list, then applies **our** SSOT-decided set.
- **Behaviour is value/flag-driven, on-the-fly:** always-loaded **dispatcher modules** read SSOT-set
  **Card-Storage flags** and branch — so a character's behaviour changes the moment we change a flag, no
  reload, no card edit. Vanilla stats (virtue, …) are **read-only input** we tap into the SSOT, never a write
  target — to make "high virtue → chaste" we activate the *behaviour module*, we don't hijack the stat.

## Where it stands (2026-06-27) — proven live
- ✅ **Instant two-world switch** (patched multi-client PPeX, mutex bypass, hide+suspend), one orchestrator,
  save-coupling, robust shutdown.
- ✅ **Transfer school → jail**: dominance combo → enslave → commit-on-save → derive jail roster; KickCard/
  AddCard; self-values + relationship memory injected.
- ✅ **AAU module binary format fully reverse-engineered** — a proven decode/encode codec; module builder.
- ✅ **The reroute hook** on `UpdateModules` — injects modules in-memory (cards pristine); native `AddModule`
  via a binary hook. Confinement proven in-game with zero card editing.
- ✅ **Stable id + SSOT re-key** — rename-proof identity; the memory DB + API keyed by it.
- ✅ **Value-gated dispatcher + Card-Storage bridge** — the gated Confinement module reads an SSOT flag set by
  `apply_state` and confines on its own: the whole value-driven evolution mechanism, proven, card-free.

**Next:** wire base-card → id at roster-build (incl. school-side card detection); build the evolution rules as
gated dispatchers (status / race-attitude / loneliness / training→transformation); calibrate thresholds.

**Hard engine limits (worked around, not removed):** 25-character roster cap, same AA2 map everywhere
(reskin + node-gating, no new geometry/verbs), no callable cold-loader (menu automation), live-reload crashes
(kill+restart), trigger *activation* is bound to card load (so on-the-fly = value-branch in an always-loaded
dispatcher, or a targeted KickCard/AddCard re-load).

## Layout
```
MWA2_V0.x/
├─ Play.bat   Create Characters.bat   Memory Tool.bat   Install.bat
├─ school/   jail/                 # game worlds (AA2 install + our AAUnlimited mods)
└─ system/
   ├─ python/        # bundled Python 3.12
   ├─ app/           # orchestrator + SSOT/memory + module codec + card tools
   ├─ ppex/   mutexfind/           # patched multi-client PPeX + multi-instance helper
   ├─ catalogs/      # module + expression catalogs
   └─ docs/  ├─ handovers/  └─ reference/
```

## Components (`system/app/`)
- `orchestrator.py` — runtime orchestrator: PPeX server, both worlds, switch, save-coupling, and the SSOT
  pipeline (commit-on-save → day-keyed journal → derive-on-load → resolver → per-char flags).
- `playthrough_db.py` — per-playthrough SQLite long-term memory (chars/rels/activity/state/confine), keyed by
  the stable id. `resolver.py` — turns the DBs into each char's active modules + Card-Storage flags.
- `module_format.py` / `module_authoring.py` — the AAU module codec + builder (e.g. the gated Confinement).
- `card_edit.py` / `card_globals.py` — read-only card inspection (cards are never written by the pipeline).
- **Lua mods** (`school|jail/AAUnlimited/mod/`): `module_reroute` (the in-memory hook), `apply_state` (sets the
  SSOT Card-Storage flags), `jail_intake` (rebuild roster from the SSOT), `master_slave`, `rel_snapshot`,
  `activity_snapshot`, `logperiod`, `orch_savename`.

## Install & run (Windows)
See **`INSTALL.md`**. In short: copy the package anywhere → run **`Install.bat`** once (Python is bundled; it
just checks the **.NET runtime**, which AA2's own PPeX needs anyway) → start with **`Play.bat`**.

## Docs
- **`system/docs/MASTER_BLUEPRINT.md`** — the all-knowledge reference: current state, a consolidated index of
  every reverse-engineered-but-unused capability, what's superseded, and a **§D module-authoring cookbook**
  (build / adapt / integrate a custom AAU trigger module end-to-end — the format was undocumented; this makes
  AI-authored custom modules reproducible). Start here.
- `system/docs/AA2_Jail_Projekt_Notizen.md` (German) — the historical design doc; **STATUS head** = overview.
- `system/docs/handovers/` — session handovers. `system/docs/reference/` — module maps + id catalog + specs.
