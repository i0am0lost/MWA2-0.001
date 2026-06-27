# MWA2 — MASTER BLUEPRINT (all-knowledge reference)

> A nothing-lost reference of **everything ever figured out** in this project — including findings that are
> **discovered but not (yet) used**, because they may matter later. Compiled 2026-06-27 from all docs in the
> old `D:\Games\MWA2` tree (handovers, the RE notes, the module/evolution maps, the main notes).
>
> **How to use this file.** Read **§A (current state)** + **§B (latent index)** + **§C (superseded)** + the **§D module-authoring cookbook** first —
> they are the *synthesis* and reflect reality as of 2026-06-27. The rest of the file is the **detailed
> preservation corpus** (four exhaustive extractions, one per doc-group), kept verbatim so no fact is lost.
> The source docs predate this session's breakthroughs, so where a source doc says something is "open/blocked",
> check §C before chasing it — several of those are already solved.
>
> Companion reference files (not duplicated here): `MODULE_ID_CATALOG.md` (full event/action/expression ids),
> `module_catalog.md` / `MODULE_CATEGORIZATION.md` (the 466-module taxonomy), `EVOLUTION_MAP.md`,
> `_re/RE_LADEFUNKTION.md` (the raw load-path RE). Living status: `AA2_Jail_Projekt_Notizen.md` STATUS head.

---

## §A. CURRENT STATE (2026-06-27) — what works, what doesn't, where we stand

### ✅ Proven (in-game / end-to-end)
- **Two-world instant switch** — patched multi-client PPeX server, AA2 single-instance-mutex bypass, inactive
  world hidden + process-suspended (no sound/CPU) + instant resume. One orchestrator, world label, in-game
  switch button, school↔jail save-coupling, robust shutdown.
- **Transfer school → jail** — dominance combo `INSULT→FIGHT→FORCE_H` enslaves; **commit-on-save** → day-keyed
  journal → derive jail roster; **KickCard/AddCard** (proven); self-values (virtue/int/str/soc) + **relationship
  memory** (continuous Sims-style snapshot) injected.
- **AAU module binary format fully RE'd** — `module_format.py` codec (932 files byte-exact decode+encode);
  `module_authoring.py` builder; full **id catalog** (events/actions/expressions).
- **★ The reroute hook** — hooks AAU's own `AAUCardData::UpdateModules`, injects modules **in-memory at load**
  (the card FILE is never touched), native `AddModule` via a binary hook. Confinement proven in-game with zero
  card editing (Luka, whose card couldn't be edited, was confined purely via the hook). RVAs/layout in §1/§RE.
- **★ Stable rename-proof identity + SSOT re-key** — an internal id; `memory.db` + `playthrough_db.py` keyed on
  it; rename-resilience proven.
- **★ Value-gated DISPATCHER + Card-Storage bridge (the evolution mechanism, proven)** — an always-loaded
  *gated* module reads an SSOT-set **Card-Storage flag** (written by `apply_state` via Lua `setCardStorage`) and
  acts on its own (gated Confinement → 3 inmates confined, others free, cards pristine). **On-the-fly, card-free,
  SSOT-driven.** This is the foundation for the whole evolution layer.
- **Clean portable package** — `MWA2_V0.1/` with deep `system/` layout, **bundled Python 3.12**, bundled
  PPeX + mutexfind, clear launchers, INSTALL.md; source pushed to GitHub `MWA2-0.001`.

### 🔧 Core architecture principles (hard rules, learned the hard way)
- **Cards are NEVER modified.** Pristine, shareable base data; one changed bit breaks the card for non-mod
  users. ALL our state is external in the **SSOT** (one `memory.db` per playthrough).
- **Identity = a stable internal id linked to the BASE CARD** (the active-roster model), never the name, never
  the seat. Same base card in different playthroughs = different evolved char; data freezes on roster-leave,
  returns on roster-return.
- **Evolution = behaviour via MODULES, not stat-writing.** We never write vanilla stats (volatile, engine-owned)
  — we tap them as read-only INPUT into the SSOT, and produce effects by activating modules / setting our own
  Card-Storage flags that gate dispatchers.
- **Behaviour on-the-fly via the dispatcher pattern**; the *set* of modules changes only at (re)load (trigger
  activation is bound to card load).

### ⬜ Open / not done (no big unknowns left except one)
- **Identity wiring `cardfile → id` at roster-build** — incl. **school-side new-card detection** (jail's AddCard
  path already knows the cardfile; school class-building does not). ⚠️ the one genuinely unexplored piece.
- **Evolution CONTENT** — the rules as gated dispatchers (status Prisoner/Ex/Rehab, race-attitude ladder,
  loneliness, training→transformation) are mostly unbuilt; resolver thresholds are placeholders.
- **Input capture** — race source from card unwired; jail-side activity capture + in-game test.
- **World mechanics** — `jail_phase` (club→end redirect) doesn't fire in-game; weekday tracking.

### 🧱 Worked-around engine walls (not removed)
- 25-character roster cap; same AA2 map everywhere (reskin + node-gating, no new geometry/verbs).
- **No callable cold-loader** — load is event/dispatch-driven inside the menu state-machine; the engine **polls**
  input (ignores PostMessage) → the only auto-load is automating a **real click** (`mouse_event`+`BlockInput`).
- **Live hot-swap over a running class crashes** (`0x10E9C8`, dangling global manager `GB+0xB6264`) → kill+restart.
- Trigger *activation* happens at card load (`InitOnLoad`) → on-the-fly = value-branch in an always-loaded
  dispatcher, or a targeted `KickCard`+`AddCard` re-load.

---

## §B. CONSOLIDATED LATENT INDEX — discovered but NOT (yet) used

The high-value "we figured this out, haven't used it" list. Each may unlock a future feature.

### B1. Engine internals / load path (from `_re/RE_LADEFUNKTION.md` — all GB-relative; GameBase is ASLR-random)
- **LOAD function `0xF3C00`** — fully RE'd, loads+activates a whole class (25 seats). Signature
  `load(ECX=wchar_t* saveName, [stack0]=data-struct)`, `ret 4`. Callable as `proc_invoke(GB+0xF3C00, name_ptr,
  data)` where `data = ptr_walk(g_var,0x18,0x28,0)`. **Explicitly viable for an in-game save-SWAP** (a world that
  already has a live class → swap is not the risky cold-start). *The richest unused lever.*
- **Wrapper `0xB2680`** (Reset+Load+housekeeping, `this` in EAX) · **`enqueueLoad` `0xB2440(context)`** (the
  nearest callable high-level entry; needs `context+0xE21C` container ≠ 0 — 0 at title menu) · **Reset/Init
  `0x413FF0`** (esi=container) · **container teardown `0x1BD5`** · **class-data-mgr init `0x455B0`** (vtable
  `0x731818`) · **per-seat activation `0x4F06E0`** (called 25×, arg 3) · **alloc helpers `0x6893A2`/`0x689a68`** ·
  **thunk H `0xB24D0`** + **dispatch loop `0x1AEEE0`** · **global manager `GB+0xB6264`** (the dangling-ptr culprit;
  reset-before-reload is the unexplored in-process rescue) · **second load fn B `~0xF41xx`** (reads .sav too;
  suspected editor/no-activation variant) · **g_var patch site `0x470B0`** · **SAVE fn `0xF36D0`** (already used
  by `extsave.lua`). Context global `0x367F48` (RVA); `this = [context+0xE29C]`, container = `[context+0xE21C]`,
  save-name std::wstring at `[edi+4]+0xE2A0`, class-data-mgr region `context+0xD774`.
- **Technique: in-engine `g_poke`-JMP-into-`x_pages` detour** — register/stack capture trampoline, DEP-aware,
  immune to anti-debug (CE stayed silent). Reusable for RE of any function that needs register-controlled args.

### B2. Module system (from the module-format / id docs)
- **`RemoveModule(int)` = DLL RVA `0x14D290`** — discovered, never used. Enables **clear+replace** (`RemoveModule(0)`
  loop + `AddModule`) = truly *ignore the card's modules* and run only ours (the ID anchor stays, orthogonal).
- **`PersistentStorage.*` likely uses the same `Serialize.h` serializer** — would let us decode/edit Card Storage
  on disk (cross-search never done; less needed now that the live bridge works).
- **Stat/status module generators** — `Set Virtue`=Action32, `Set Card Storage`=Actions24-27, all stat setters
  (Actions32-45). `module_authoring.py` can build them; not generated. The Card-Storage get/set ids are the
  generic SSOT bridge for *any* status module.
- **Control-flow primitives** — Delayed Execution (Event27), For Loop/Conditional Jump (Action9/5) for richer modules.

### B3. Lua API surface (hooks/idioms found, several never exploited)
- `on.plan`, `on.ui_event`, `on.d3d9_preload`, `SetPlayerCharacter`, `createHStatsDump`/`restoreHStatsFromDump`
  (H-stats dump-restore — not wired into transfer), `as.answerChar.m_lastConversationAnswerPercent` (action
  success-%, geass forces 999), the `0x470B0` g_var-patch anchor (reusable for any save-name/period read).

### B4. Evolution / taxonomy design (from MODULE_CATEGORIZATION / EVOLUTION_MAP / the notes backlog)
- **Module taxonomy:** 466 modules on 7 axes — **TARGET 104 / GATE 13 / SOURCE 316**, **259 developable**. The
  TARGET outcome ladders (Corruption→Sex Addict, predator/yandere/violence, purity counter-axis, training,
  pregnancy) are the menu of evolution endpoints.
- **★ Race-standing escalation engine** — `char_race`/`char_race_xp` DB **built + unit-tested but rules UNWIRED**:
  24 races × 5 valences; negative ladder neutral→**Prejudice→Hunter→Natural Enemy→Slayer**, positive
  neutral→**Bias→Obsession**; driven by domination (→neg) vs loving-H (→pos) per partner race. 168 race modules.
  *Largest specified-but-unbuilt block.*
- **Slave-progression module** (unbroken→broken→trained) — explicit placeholder that **doesn't exist yet, must be
  built like Prisoner**. Downstream ideas: **Slave-Market / Breed-Room**.
- **Lineage / reincarnation** — `parent_id` invariant + the **`Undying`** module (a child/successor inherits id-linked
  ancestry). **Loneliness/Loner** from `social_wealth` (bonds≥3 threshold). **Status** Prisoner/Ex-Prisoner/Rehabilitated.
- **~7-day Auto-Save safety net** — auto-save at day-change so a player who never saves still commits transfers.
- **Daily background tick** (offline resolver) for world-independent evolution/homecoming scenarios.

### B5. World mechanics & scaling (from the notes §9b / §8b)
- **Worlds-as-config** (switch/transfer/memory parametrized by world-id) → each new world ≈ a config entry + a
  reskin. **RAM-adaptive load strategy** (how many worlds preloaded). **Installer** (find AAU install → junctions
  for shared heavy data → Lua patches → patched `PPeXM64` with original backup → custom modules + assets + save
  templates → DB → config). **jail-night-only** (`on.period`-hold), **node-blocking progressive dungeon**, reskin.

### B6. Day-phase machine & end-day resolver (notes §3.2 / §3.3 — partly solved, partly latent)
- **Phase sequence is data-driven / variable, NOT a rigid 1..10** — a live `4→7` skip was logged (phases 5 sports +
  6 2nd-break skipped) with timewarp disabled = the vanilla engine. So per-world rhythms (e.g. a "single-phase jail")
  are realizable through the phase system. Clean lever = `timewarp.lua` = the `on.period(new,old)` set-hook (see B3).
- **[LATENT] controllability indicators (user-observed, unverified — `CurrentPeriod`-on-Sunday log not yet run):**
  (a) **Sunday** reportedly has a different phase count/structure than a schoolday → "different phase schemata"
  already exist internally; (b) **Dates** consume more time / modify day-flow at runtime (by action, not weekday) →
  smells like a controllable mechanism; (c) **Vanilla Ver.6 patch** added control for **PC/NPC movement speed, field
  speed, and "set end time"** — a real engine-exposed time/speed lever, never exploited.
- **[LATENT] End-day resolver plan (notes §3.2, designed but unbuilt):** trigger polls `CurrentPeriod`; on transition
  (8/10) writes a flag (Card Storage / Global Var) *or* the save modification-timestamp flips → a Python watcher reads
  it → runs transfer + background-reload of the hidden instance. **Needs an exactly-once-per-day guard** (set/reset a
  flag, else it double-fires). **Engine-independent fallback:** Python file-watcher on the save's modification-timestamp
  (flips on sleep) — coarser, but needs no engine hook at all.
- **Teleport redirect is reactive-catchable** — let phases tick, intercept every unwanted room-change ("PC in
  jail-world? → send back") = the jailer principle applied to the PC; player sees a continuous jail phase though
  phases run internally.

---

## §C. SUPERSEDED / RESOLVED — source docs say "open", but it's solved (don't chase)

- **"Modules only fire if In-Use on a card" / "module doesn't load" (HANDOVER_confinement, cause B)** →
  **SOLVED** by the reroute hook: it injects the module into the live `m_modules` in-memory before `InitOnLoad`,
  so it activates regardless of what the card lists.
- **"Cause A: Card-Storage location mismatch" (Lua `setCardStorage`→Class Storage ≠ engine Card Storage)** →
  **SOLVED/PROVEN MOOT**: the gated dispatcher reads the engine "Get Card Storage" expression and **sees exactly
  what `apply_state`'s `setCardStorage` wrote** — the bridge works as-is; no native `storeCard` hack, no Class
  Storage (BOOL46/INT121) workaround needed.
- **"Write modules onto cards" / "external card edit at the day boundary" / "card-tag / mwa_id-on-card"** →
  **REJECTED.** Cards are never modified. The byte-splice corrupts cards (the `AUSS` coupling). Identity is
  `cardfile→id` in the SSOT; modules are injected in-memory by the hook.
- **resolver `MODULE_EFFECTS` (writing virtue=0 etc. onto chars)** → **REMOVED.** We never write vanilla stats;
  `apply_state` only sets Card-Storage flags; the resolver outputs the module set + flags.
- **Confinement Stage-2 "gated, later"** → **BUILT and live** (`build_confinement_gated`, the gated dispatcher).
- **mwa_id-flag reroute (`_orch_reroute.flag`, hook reads card-stamped id)** → superseded by the corrected
  active-roster model (the builder knows cardfile→id; the hook no longer reads a stamped id). Dead-flag removed.

> Still genuinely open (carried forward): in-game save-SWAP via `0xF3C00` (B1) was never tried productively;
> the race engine (B4) is built-but-unwired; cold-load remains impossible (real-click automation is the answer).

---

## §D. MODULE AUTHORING COOKBOOK — build / adapt / integrate a custom AAU module

> This is the self-contained recipe that makes **AI-authored custom modules** possible. The AAU trigger-module
> binary format was undocumented (people sell "custom modules" because of that); we reverse-engineered it into a
> proven codec + builder + id catalog. Given a desired behaviour, an AI can follow this section end-to-end to
> produce a working module and wire it into our SSOT system — **without ever touching a card** (modules live in
> `data/override/module/` and are injected in-memory at load by the reroute hook).
>
> Files: builder `system/app/module_authoring.py` · codec `system/app/module_format.py` · full id vocabulary
> `system/docs/reference/MODULE_ID_CATALOG.md` (+ raw `system/catalogs/_expr_catalog.json`) · the 466 existing
> modules (names+descriptions, for reuse/adaptation) `system/catalogs/module_catalog.md`.

### D.1 Mental model (what a module IS)
A module is a tree:
```
Module   = { name, description, triggers[] , globals[], dependencies[] }
Trigger  = { name, events[] , vars[], guiActions[] }          # fires when ANY of its events occurs
GUIAction= { action, subactions[] }                            # the If/then tree
Action   = { id, params[] }                                    # "do something" (id from the ACTIONS table)
Expression= { type, id, params[] }  | const(type,val) | var(type,name)   # "read a value / a condition"
```
- An **event** = WHEN the trigger fires (e.g. Room Change, H Ends, A Period Ends, Card Added).
- A **condition** = an Expression returning BOOL, placed as the param of an **`If` action** (`AC_IF`); the If's
  `subactions` run only when it's true. Nest `If`s / use `Logical And/Or` to combine.
- An **action** = WHAT happens (move NPC, set Card Storage, set virtue, start H, add love points, …).
- **You can only use EXISTING events/actions/expressions** — the engine has no new verbs. The full menu is the
  id catalog; that menu is large enough for almost anything (see ACTIONS 1–65, EXPRESSIONS per return-type).

### D.2 The vocabulary (ids) — where to look
- **EVENTS** (id = enum value): 6 Card Added("Init") · 7 A Period Ends · **16 Card Changes Room** · 22 H Ends ·
  23 H Starts · 26 Relationship Points Changed · 27 Delayed Execution … (full list: MODULE_ID_CATALOG.md / corpus §3).
- **ACTIONS** (id = 1-based): 2 If · **20 Make Npc Move to Room(seat,room)** · **24–27 Set Card Storage Int/Float/
  String/Bool(seat,key,val)** · 28–31 Remove Card Storage · **32 Set Virtue** · 33 Set Trait · 51 Start H scene ·
  12–16 Add Love/Like/Dislike/Hate/Points … (full list: MODULE_ID_CATALOG.md).
- **EXPRESSIONS** (id = 1-based **within return type**; every type starts 1=Const 2=Var 3=Enum):
  - →INT: **9 Triggering Card · 10 This Card · 55 Player Character · 97 Current Room(seat)** · 24 Get Card Storage
    Int(seat,key,def) · 25 Virtue · 47 Days Passed · 49 Current Period · 121 Get Class Storage Int …
  - →BOOL: **4 And · 5 Or · 8 Equal · 11 Not · 13 Not Equal** · 6 Greater · 24 Get Card Storage Bool(seat,key,def) …
  - →FLOAT: 10 Get Card Storage Float. →STRING: 7 Get Card Storage String · 8 + (concat).
- The verified constants are already in `module_authoring.py` (extend it as you use more ids).

### D.3 Build from code (the proven workflow)
Using `module_authoring.py` helpers (`const/var/expr`, shorthands `this_card/triggering_card/pc/current_room/
eq/neq/land`, `action/gui/event/trigger/module`) + `module_format.encode`:
```python
import module_format as mf
from module_authoring import (const, expr, action, gui, event, trigger, module,
    this_card, triggering_card, pc, current_room, eq, neq, land,
    AC_IF, AC_NPC_MOVE_ROOM, EX_INT_GET_CARDSTORAGE_INT, EX_BOOL_GET_CARDSTORAGE_BOOL, EV_ROOM_CHANGE)
from module_format import T_INT, T_BOOL, T_STRING

# WORKED EXAMPLE — the live, SSOT-gated Confinement (build_confinement_gated):
def cardstorage_int(seat, key):   return expr(T_INT,  EX_INT_GET_CARDSTORAGE_INT,  seat, const(T_STRING,key), const(T_INT,0))
def cardstorage_bool(seat, key):  return expr(T_BOOL, EX_BOOL_GET_CARDSTORAGE_BOOL, seat, const(T_STRING,key), const(T_BOOL,False))

this = this_card()
cond = land( land( eq(this, triggering_card()),          # I'm the one who moved
                   cardstorage_bool(this,"confined") ),  # AND the SSOT flagged me confined
             neq(current_room(this), cardstorage_int(this,"cell")) )  # AND I'm outside my cell
move = gui(action(AC_NPC_MOVE_ROOM, this, cardstorage_int(this,"cell")))   # -> send me back to my cell
trig = trigger("Confine", [event(EV_ROOM_CHANGE)], [ gui(action(AC_IF, cond), subs=[move]) ])
m = module("Confinement", "SSOT-gated jail confinement: inert until Card Storage 'confined'=true.", [trig])

data = mf.encode(m)
assert mf.decode(data) == m and mf.encode(mf.decode(data)) == data    # self-roundtrip (REQUIRED)
open(r"<world>\data\override\module\Confinement", "wb").write(data)    # name = file name, no extension
```
Key rules: a module's **file name = the module name, no extension**, in `data/override/module/`. The codec is
byte-exact; the `assert` roundtrip is the first validation gate.

### D.4 Adapt an existing module (often easier than from scratch)
Any of the 466 modules can be a starting point: `m = mf.decode(open(path,'rb').read())` → it's a plain dict →
edit (swap an action, change a threshold const, add a condition, retarget a room) → `mf.encode(m)` → write.
Use `module_catalog.md` to find a module whose behaviour is close, decode it, and tweak. (Confinement was
authored fresh because no existing module pinned an NPC to a node — but most behaviours have a near match.)

### D.5 Integrate into OUR system (the part that makes it useful)
A module on disk does nothing until it's (a) active on a char and (b) gated by our data. Two patterns:

**(A) Value-gated DISPATCHER — the default, on-the-fly, card-free (PROVEN).**
1. Build the module **gated on Card-Storage flags** (conditions use `Get Card Storage Bool/Int` like the
   Confinement example). It is INERT until the flag is set, so it's safe to put on every char.
2. The **reroute hook** (`module_reroute.lua`, on `AAUCardData::UpdateModules`) injects it in-memory on every
   card at load (add its name to the `DISPATCHERS` list). Cards are never written.
3. The **SSOT sets the flag**: `resolver.py` decides per char → `orchestrator.write_char_state` emits the
   `@b:key=…;@i:key=…` Card-Storage flags into `_orch_char_state.flag` → `apply_state.lua` calls
   `setCardStorage(seat,key,val)`. The module's "Get Card Storage" expression reads exactly that (the bridge
   works). → change the flag (no reload) → the module branches to a different path next time its event fires.

**(B) Direct behaviour module** (an existing AAU personality module, e.g. "Sex Addict"): the SSOT decides which
chars should have it; the reroute hook injects it per char at load (structural — changing the *set* needs a
re-load: KickCard+AddCard or a world (re)load). No stat-writing — the module's own behaviour produces the effect.

### D.6 Validation ladder
1. **Codec roundtrip** `decode(encode(m))==m` (in the build, mandatory).
2. **Editor ground-truth** (optional): open the generated module in the AAU Trigger Editor — does it render the
   intended If/then logic?
3. **In-game**: inject via the hook, set the gating flag from the SSOT, observe the behaviour. The hook debug
   log `jail/_orch_reroute_debug.flag` confirms injection; `apply_state` debug confirms the flag was set.

### D.7 Constraints & gotchas (so the module actually works)
- **Existing verbs only** — no new actions/events/expressions; pick from the catalog.
- **Reactive, not preventive** — you react to an event (e.g. Room Change) and correct; there is no "block movement"
  primitive (`m_forceAction` is not Lua-reachable; `Make Npc Move to Room` just sets `movementType=2;roomTarget`).
- **PC self-exclusion** — gate NPC-only behaviours with `This Card != Player Character` (PC = seat with the green
  "Pc" badge; behaviour modules on the PC are usually inert anyway).
- **Cards are NEVER modified** — never splice a module onto a card file (corrupts the `AUSS` coupling); modules
  live in `data/override/module/` and are applied at runtime.
- **Flags are the SSOT→module channel** — Card Storage (`setCardStorage` ↔ "Get Card Storage" expression) is the
  proven bridge; use it for anything the engine has no native value for. Vanilla stats = read-only input.
- Trigger activation is bound to card load (`InitOnLoad`); a module added to an already-loaded char only activates
  if added during the hook (before activation) — which the reroute hook does.

### D.8 AI recipe (given a desired behaviour → a working, integrated module)
1. **WHEN** — pick the event(s) (Room Change / H Ends / Period Ends / Card Added / Relationship Changed / …).
2. **IF** — express the condition from expressions, AND-ed with the **SSOT flag** that should gate it
   (`Get Card Storage Bool('<your_flag>')`), plus `This Card == Triggering Card` and PC-exclusion as needed.
3. **DO** — pick the action(s) (move/Set Card Storage/Set Virtue/Start H/Add Points/…), nest under the `If`.
4. **BUILD** with `module_authoring.py`, **encode**, **roundtrip-assert**, write to `data/override/module/<Name>`.
5. **GATE** — add `<Name>` to the reroute hook's dispatcher list (or have the resolver select it per char); have
   the resolver emit `@b:<your_flag>=1` for the chars who should get the behaviour; `apply_state` sets it.
6. **VALIDATE** — roundtrip ✓, inject ✓ (hook log), flag set ✓ (apply log), behaviour ✓ (in-game).
This is exactly the "custom module on demand" capability — now reproducible by any AI from this blueprint.

---

# DETAILED PRESERVATION CORPUS

Below: the four exhaustive per-doc-group extractions (RE/format · handovers · design/taxonomy · main notes),
kept in full so nothing is lost. Synthesis above; raw detail below.


---

# CORPUS 1/4 — RE & BINARY FORMAT (detailed extraction)

# Master-Blueprint Source Extraction — RE / Binary-Format Facts

Exhaustive extraction from four RE/format docs in `D:\Games\MWA2`. Verbatim hex/offsets/names preserved.
Citations as (file → section). Capability discovered-but-unused flagged **[LATENT]**; dead-ends **[REJECTED]**.

> **GLOBAL REBASING NOTE (load everywhere):** `peinfo.py` uses file ImageBase **`0x400000`** (preferred base).
> Runtime `GameBase` is **ASLR-randomized** per launch (observed: `0x6C0000`, `0x4D0000`, `0xA20000`). Always compute
> GB-relative. Runtime VA = peinfo-RVA + GameBase. Absolute operands in disasm are **file-VA** (preferred base) → subtract
> `0x400000` to get RVA, then compare to runtime via the current GB delta. (Cited: RE_LADEFUNKTION → TEST-RUNDE 4, #7 practical hint.)

---

# 1. `_re\RE_LADEFUNKTION.md` — Save-LOAD function RE of AA2Play.exe

## 1.1 Facts — known starting points & PE layout

- **SAVE function already called in shipped mod:** `mod/extsave.lua` does `proc_invoke(GameBase+0xF36D0, 0, data)` (`quicksave`).
  (→ BASIS-KONTEXT, RE-STARTPUNKTE)
- `data = ptr_walk(g_var, 0x18, 0x28, 0)`; `g_var` set up via memory-patch at RVA **`0x470B0`**. (→ RE-STARTPUNKTE)
- Save NAME in struct at offset **+100** (unicode) = `+0x64`. (→ RE-STARTPUNKTE)
- AA2Play.exe imports `CreateFileW`/`ReadFile`. Saves live at `<world>\data\save\class\*.sav`. (→ RE-STARTPUNKTE)
- Tool `_re/peinfo.py` (Python 3.12.8, capstone 5.0.7 + pefile 2024.8.26): modes `overview` / `<rva> [n]` /
  `xref <iat>` / `callers <rva>`. **Use `python`, NOT `py`/3.14 (broken stub).** (→ UMGEBUNGS-HINWEIS, STATUS)

### F1 — PE layout AA2Play.exe (32-bit) (→ FUNDE F1)
- `ImageBase = 0x00400000`, EntryPoint RVA `0x0028EFDE`, Machine x86.
- Sections: `.text` RVA `0x1000` vsize `0x2E161A` (code RVA 0x1000…~0x2E261A; `0xF36D0` is in `.text`).
  `.rdata` `0x2E3000`, `.data` `0x355000`, `.rsrc` `0x3AB000`, `.reloc` `0xD02000`.

### F2 — IAT slots (absolute VA @ ImageBase 0x400000) (→ FUNDE F2)
| Function | IAT VA (`call dword [VA]`) | RVA |
|---|---|---|
| ReadFile | `0x006E3218` | 0x2E3218 |
| WriteFile | `0x006E3214` | 0x2E3214 |
| CreateFileW | `0x006E31B0` | 0x2E31B0 |
| CreateFileA | `0x006E3264` | 0x2E3264 |
| SetFilePointer | `0x006E31EC` | 0x2E31EC |
| SetFilePointerEx | `0x006E3234` | 0x2E3234 |
| GetFileSize | `0x006E31C4` | 0x2E31C4 |
| CloseHandle | `0x006E3184` | 0x2E3184 |

### F3 — SAVE function @ RVA `0xF36D0` (VA `0x4F36D0`) — fully understood (→ FUNDE F3)
- ABI: `sub esp,0x248` + stack-canary `[0x763AA0]`. Reads `ebp = [esp+0x254]` = the **`data` arg** (stack arg).
  Call form `proc_invoke(GameBase+0xF36D0, 0, data)` → `data` = 1st stack arg → lands in `ebp`. `this`(=0) unused. Returns `al`.
- Path build: name at `[ebp+0x64]` (unicode) → helper `call 0x598140` (args: `0x104`=MAX_PATH, format-string `0x71C6BC`,
  dir `0x728328`, name) → full `.sav` path.
- Open: `CreateFileW` (`call [0x6E31B0]`) @ `0xF3791`, `GENERIC_WRITE 0x40000000`, share `FILE_SHARE_WRITE 2`,
  `CREATE_ALWAYS 2`, attr `0x80`. Handle in `edi`.
- Write: `esi = [0x6E3214]` = WriteFile, repeated `call esi`:
  1. 4 bytes magic/version `0x65` (stack-local)
  2. `[ebp+0x04]` len `0x40`
  3. `[ebp+0x44]` len `0x10`
  4. `[ebp+0x54]` len `0x10`
  5. loop over array `obj=[ebp+0x394]`, `begin=[obj+0x6C]`, `end=[obj+0x70]`, element-size 4 (pointer) = char/seat list.
- **Save-struct layout (data = ebp):** `+0x04`(0x40B) · `+0x44`(0x10B) · `+0x54`(0x10B) · `+0x64`=Name(unicode) ·
  `+0x394`=Ptr→{`+0x6C`=begin,`+0x70`=end} char-array · `+0x398`=validity-ptr (≠0 required).
- Save fn ends exactly at `0x4F3B24: ret 4`. Then helper `0x4F3B30`, then at `0x4F3C00` the LOAD function.

### F4 — Xref scan (→ FUNDE F4)
- ReadFile (`[0x6E3218]`) — 11 call-sites; just after Save: `0xF3D17`, `0xF41F8`.
- CreateFileW (`[0x6E31B0]`) — 25 call-sites; near Save: `0xF3791` (Save WRITE), `0xF3C9F` (Load-A READ), `0xF41BB` (Load-B READ).
- → Two load-like functions after Save: **A @ `0xF3C00`** and **B @ ~`0xF41xx`**.

### ★ F5 — LOAD function (main result) @ RVA `0xF3C00` (VA `0x4F3C00`) (→ FUNDE F5)
Mirror of Save `0xF36D0`. Proof chain:
- Prolog: SEH-frame (`push -1; push 0x6DEA0C; push fs:[0]`) + stack-canary `[0x763AA0]`, `sub esp,0x224`.
- `mov ebp,[esp+0x248]` = stack-arg = `data` struct; checks `[ebp+0x398]≠0` (same validity field).
- `mov edi,ecx` → **ECX = `wchar_t* saveName`**; copied into `[ebp+0x64]`.
- Path build: same helper `call 0x598140`, format-string `0x71C6BC`, dir `0x728328`.
- `CreateFileW` @ `0xF3C9F`: `GENERIC_READ 0x80000000` · `FILE_SHARE_READ 1` · `OPEN_EXISTING 3` (read path).
- `GetFileSize` @ `0xF3CEE` (`[0x6E31C4]`) → buffer alloc (`call 0x6893A2`) → **`ReadFile` @ `0xF3D17`** (`[0x6E3218]`).
- **Activation:** end loop `esi = 0..0x18` (= **25 seats**), per seat `call 0x4F06E0` (args incl. `3`), then
  `[ebp+0x37D]=1` (loaded-flag), `[ebp+0x270]=[0x7A4B94]`. → loads + activates whole class (not a preview).
- **Epilog `0x4F403D: ret 4`** → exactly 1 stack arg (the data-struct); ECX (name) doesn't count.
- **SIGNATURE:** `load(ECX = wchar_t* saveName, [stack arg0] = data-struct)` ; ret 4, thiscall-like.
  `proc_invoke(GameBase + 0xF3C00, <name_ptr>, <data_struct>)`.
  `data = ptr_walk(g_var,0x18,0x28,0)` (same struct ptr as extsave; g_var via patch @ `0x470B0`).
  `name_ptr` = ptr to UTF-16 string e.g. `"class0001.sav"`.

### F7 — sole caller of `0xF3C00` = wrapper `0xB2680` (the "load class" routine) (→ FUNDE F7)
`peinfo.py callers 0xF3C00` → exactly 1 E8-caller @ `0xB26AC`, in function from `0xB2680`:
```
0xB2680  sub esp,0x24 / push esi,edi
0xB2685  mov edi, eax          ; EAX = THIS (central save/game-state object, set by caller)
0xB2687  mov esi,[edi+0x1c]    ; container object
0xB268A  call 0x413FF0         ; Reset/Init BEFORE load (clears container)
0xB268F  mov eax,[edi+4] / add eax,0xE2A0   ; std::wstring field "save-name to load"
0xB269B  cmp [eax+0x18],8 / jb ...          ; MSVC SSO check (len>=8 → heap-ptr, else inline)
0xB269D  mov ecx,[eax+4]  |  0xB26A2 lea ecx,[eax+4]   ; ECX = name buffer (wchar_t*)
0xB26A5  mov eax,[edi+0x1c] / mov edx,[eax+0x28] / push edx   ; data = [[edi+0x1c]+0x28]
0xB26AC  call 0x4F3C00        ; load(ECX=Name, stack=data)
0xB26B1+ ... further setup (push 3,1,0; zero a stack-block) = post-processing
```
- Signature 100% confirmed: ECX = wchar_t* name (std::wstring buffer); 1 stack arg = data; `ret 4`.
- `data`-pointer chain last hop `[container+0x28]` = identical to extsave `ptr_walk(g_var,0x18,0x28,0)`.
- Wrapper `0xB2680` = **`ret 0`**, `this` in **EAX** (`mov edi,eax`). First 5 bytes `83 EC 24`(sub esp,0x24) + `56`(push esi) +
  `57`(push edi); clean boundary at `0xB2685`. (→ STATUS Runde 3, F7)
- Reset `0x413FF0` reads its object from **ESI** (non-standard convention; esi=container at the `0xB2680` call-site).
  `proc_invoke` only sets ECX+stack, NOT esi → plain `proc_invoke` cannot drive the reset. (→ TEST-RUNDE 2)
- `0xB2680` housekeeping after load: `0x5ADB70` (func-ptrs `0x439xxx`), `0x5ADEC0`(500,500,...), event-queue `[this+0x7f9/0x7fc]` — all `this`-based, post-load (UI/events). (→ TEST-RUNDE 2)

### F9 — path/name format + Lua building-blocks (→ FUNDE F9)
- Helper `0x598140`: format-string `0x71C6BC` = **`"%s%s"`** (wide), dir `0x728328` = **`"data/save/class/"`** (wide).
  Full path = `data/save/class/<name>`; **`<name>` includes `.sav`**.
- Real save names (CJK, UTF-16): `Athena学園1年1組.sav`, `NEW HOPE学園1年1組.sav`, `Illusion 1学園1年1組.sav`.
- Lua blocks (verified in font.lua/fakereg.lua): `utf8_to_unicode(utf8.."\0")` → UTF-16 bytes; `strdup(...)` →
  persistent native copy (returns `wchar_t*`). `data = ptr_walk(g_var,0x18,0x28,0)`. `proc_invoke(addr,this,...)` sets
  ECX=this, pushes the rest.

### The Live-Reload WALL — diagnosed cause (→ STATUS, TEST-RUNDE 4)
- Reload OVER a LIVE class crashes @ RVA **`0x10E9C8`** (`cmp [esi+0x3c],edx`, AV READ on `0x215CCD9C` = esi+0x3c, esi dangling).
- Faulting fn reads global `[GameBase+0xB6264]`, iterates list `[+0x20]..[+0x24]`, per element `esi=[[elem]+0xE0]`, checks `[esi+0x3c]`.
  An old card holds a stale `[+0xE0]` sub-object pointer.
- Call-chain (RVA): wrapper `0xB26B1` (after `call 0xF3C00`) → load `0xF3EFE` → … → crash `0x10E9C8`.
- v2 (isolated Reset+Load) and v3 (full wrapper) crash IDENTICALLY @ `0x10E9C8` → housekeeping/`this` was never the problem.
  Global manager `GameBase+0xB6264` (card/interaction/trigger cache) keeps dangling ptrs to old cards' sub-objects; the
  wrapper does NOT reset it — only the higher menu-load state-machine does.

### Cold-menu chain emptiness (key finding, #7) (→ #7 MESSERGEBNISSE Diag table)
| Time | anchor=[g_var] | container | data | this |
|---|---|---|---|---|
| Main menu (cold) | 0 | 0 | 0 | 0 |
| in-game (after load) | 0x25D616B0 | 0x17672E40 | 0x1D388A80 | 0x1C4FE1F8 |
- In-game consistent: `container == [this+0x1c] == data+0x394` (CharArr-Obj).
- **At main menu the whole chain is EMPTY.** Container is created BY the load itself → cold-load via g_var/`0xF3C00`/`0xB2680` impossible (nothing to load into).

### #7 deep-RE — event/load system resolved (→ #7 TIEFEN-RE)
Context-global **`0x767f48`** (file-VA; RVA `0x367f48`). New RVAs (file base 0x400000):
- **Thunk `H` @ `0xB24D0`** (only path to 0xB2680, via `E9 jmp` @ `0xB24DE`):
  `mov eax,[esp+4]`(=context) · `mov eax,[eax+0xE29C]`(=this) · `test;je` · `jmp 0xB2680`. → **`this = [context+0xE29C]`**.
- **`enqueueLoad` @ `0xB2440`** — `func(context)`: `new(0x30)` (`call 0x689a68`) → ctor `0x4b2390` → `mov [context+0xE29C], eax`.
- **Ctor `0x4b2390`** (eax=new obj, ecx=context): `[obj]=vtable 0x72842c` · `[obj+4]=context` ·
  **`[obj+0x1c]=[context+0xE21C]`** (container, COPIED) · fields `[obj+0x18..0x28]` from `context+0xD774` region · `[obj+0x2c]=0`.
- **Dispatch-loop @ `0x1AEEE0`** runs a callback-table per tick, each arg `0x767f48`; one entry = `H`. Sibling @ `0xB24A0`
  clears slot after run (`mov [esi+0xE29C],0`).
- **`this = [context+0xE29C]`** — NOT a persistent singleton; created as 0x30-byte heap obj (vtable `0x72842c`) by enqueueLoad; 0 at title menu.

### #7 container-lifecycle (→ #7 Container-Lifecycle)
- Container-slot `0x776164` (=context+0xE21C): only absolute write is `0x1BD5: mov [0x776164], edi` with `edi=0` = teardown
  (frees container via virtual dtor `call [[ecx]](1)` + null slot). Displacement `+0xE21C` → only reads (`0x74200`, `0xF09D4`).
- `context+0xD774` sub-struct = "class-data-manager"; init @ **`0x455B0`** sets `+0xa9c=vtable 0x731818`,
  `+0xaa0/aa4/aa8/aac/ab0/ab4=-1`, `+0xab8/abc=0`. Container-slot `+0xaa8`(=context+0xE21C) set to `-1`, not an object.
- **No single "alloc container; store" point**; container is woven into the class-data-manager lifecycle (vtable 0x731818).

### #7 dynamic (Cheat Engine + mod-detour) (→ #7 DYNAMISCH)
- `enqueueLoad`-CALLER = RVA **`0x1AF4FC`** (SYNCHRONOUS at load-click). this=0x1A972248, container=[this+0x1c]=0x16A823C8
  (matches g_var-chain container → container addr `context+0xE21C` confirmed correct; CE BP silence was a CE/anti-debug issue).
- Disasm @ `0x1AF4FC`: menu-action dispatch (`call [edi]` arg `0x600`; `rep movsd` 9 dwords = save-name → `[ebx+0x10]`;
  `call 0x5AF720`; `mov edx,[edx+8]; push ebp(=context); call edx` = enqueueLoad).
- **Synchronous call chain** (GB=0xA20000, only `.text` returns):
  `enqueueLoad(0xB2440) ← 0x1AF4FC ← 0x1AE2AC ← 0x1ADCE7 ← 0x1AEF52` — entire chain in `0x1AD000–0x1AF000`
  (menu/scene state-machine). No standalone parametrized `load(saveName)` frame.
- Menu state fields: `0x1ADCE7`: `mov eax,[esi+0x7F4]; cmp eax,3/4…` → `[Menu+0x7F4]` = screen-state. `0x1AE2AC` sets `[esi+0x7EC]`.
  Save-name from list-selection `rep movsd` 9 dwords @ `0x1AF4CE`.
- **Polled mouse input:** synthetic clicks worked only with the button HELD ~0.25s → game polls button state (DirectInput-like),
  ignores `WM_LBUTTONDOWN` → PostMessage injection impossible; only real device input (`mouse_event`/`SetCursorPos`) drives the menu.

## 1.2 [LATENT] — capabilities found but NOT used (RE_LADEFUNKTION)

- **[LATENT] LOAD function `0xF3C00`** — fully RE'd, proven to load (loads class + fires init triggers), but its productive use
  was abandoned for live-reload (crashes) and cold-load (empty container). Still callable as
  `proc_invoke(GameBase+0xF3C00, name_ptr, data)` in any context where a container already exists — explicitly noted as
  **viable for the safe in-game save-SWAP** (jail instance already has a live class → swap is not the risky cold-start).
  (→ ARCHITEKTUR-IDEE; F5/F7). This is the richest unused lever.
- **[LATENT] Wrapper `0xB2680`** (full Reset+Load+housekeeping) — RE'd, `this` in EAX, capture-detour design written (v3),
  proven it runs the full game flow. Unused because live-reload hits the `0xB6264` wall; would be usable for a same-world swap.
- **[LATENT] `enqueueLoad` @ `0xB2440(context)`** — identified as the nearest *callable* high-level entry; engine "builds the
  rest itself" once container+name are in the context. NOT used because at title-menu the container (`context+0xE21C`) is 0.
  Would become a clean cold-load IF the container-allocation point were found: `ensure container` → name → `proc_invoke(GB+0xB2440, context)`.
- **[LATENT] Container teardown `0x1BD5`** (`mov [0x776164], edi`, edi=0, virtual dtor) — found, not exercised; relevant if one
  ever wants to programmatically release/reset the container.
- **[LATENT] Class-data-manager init `0x455B0`** (vtable `0x731818`, sets slots to -1) — the manager-init entry; a building
  block for a hand-rolled cold-load lifecycle (deemed too fragile to pursue).
- **[LATENT] Reset/Init `0x413FF0`** (esi=container) — container reset; only reachable via a register-controlled stub (esi),
  not plain `proc_invoke`. Noted as optionally needed before `0xF3C00` if stale-state appears on same-world swap.
- **[LATENT] Second load function B @ ~`0xF41xx`** (CreateFileW@`0xF41BB`, ReadFile@`0xF41F8`) — exists, also reads `.sav`,
  suspected variant (load without full activation / editor path). Never disassembled in detail; reserved as fallback to A.
- **[LATENT] Save activation primitive `0x4F06E0`** (per-seat, called 25× with arg `3`) — the per-seat activation call; noted but not independently used.
- **[LATENT] Buffer-alloc helper `0x6893A2`** and **`0x689a68`** (`new(0x30)`) — allocation helpers identified in the load/enqueue paths.
- **[LATENT] Thunk `H` @ `0xB24D0`** and **dispatch-loop `0x1AEEE0`** — the registered tick handler + callback table; the actual
  dispatch mechanism, mapped but not invoked.
- **[LATENT] Global manager `GameBase+0xB6264`** (card/interaction/trigger cache) — the dangling-pointer culprit; noted as the
  thing one *could* reset before a live-reload ("rabbit-hole, not recommended") — an unused in-process rescue path.
- **[LATENT] g_var patch point `0x470B0`** — the memory-patch site that sets up `g_var` (shared by extsave + loadtest). Reusable anchor.

## 1.3 [REJECTED] — dead-ends with reasons (RE_LADEFUNKTION)

- **[REJECTED: empty container at menu] Cold-load via direct function call (`0xF3C00`/`0xB2680`/g_var).** At the title menu
  anchor/container/data/this are all 0; the container is created by the load itself. (→ #7 MESSERGEBNISSE)
- **[REJECTED: load is event/dispatch-driven, not a callable] No callable internal "load(saveName)" entry exists.** The whole
  synchronous chain `0xB2440 ← 0x1AF4FC ← 0x1AE2AC ← 0x1ADCE7 ← 0x1AEF52` lives inside the menu/scene state-machine; container
  creation + name + enqueue are all woven into that flow. Proven both statically and dynamically. (→ #7 DEFINITIVES ERGEBNIS)
- **[REJECTED: dangling cross-class globals] Live hot-swap over a running class** — crashes @ `0x10E9C8`; manager global
  `0xB6264` not reset by the wrapper. Out of scope → use Kill+Restart. (→ TEST-RUNDE 4)
- **[REJECTED: inconsistent partial state → crash class] State-poke of menu fields** (`[Menu+0x7F4]` etc.) — real input sets
  multiple state fields consistently; a partial poke = crash class. More work, less robust. (→ #7 ABSCHLUSS)
- **[REJECTED: engine polls input] PostMessage / WM_LBUTTONDOWN injection** — engine polls button state; only real device input works. (→ #7 ABSCHLUSS)
- **[REJECTED: CE silent on data-write BP] Cheat-Engine "find out what writes" on the container slot** stayed silent
  (mechanics/anti-debug). Mod-detour used instead (in-engine, immune). Address was correct. (→ #7 DYNAMISCH, CE-Notizen)
- **[REJECTED: broken interpreter] `py` / `C:\Python314\python.exe`** for RE tooling — stub without Lib/site-packages/encodings.
  Use `python` (3.12.8). (→ UMGEBUNGS-HINWEIS)
- **★ FINAL DECISION:** "replace clicking with a function call" = not possible. The only consistent auto-load mechanism for a
  polled-input engine = automate a real click (Weg B: `mouse_event` + `BlockInput`) in the orchestrator. (→ #7 ABSCHLUSS)

## 1.4 Open questions (RE_LADEFUNKTION)

- Who writes `context+0xE21C` (container alloc / "enter game state" init)? — the single last open static question (Q2/Q5).
- Does the high-level handler reset `0xB6264`? — undetermined (depends on the unfound container-alloc/top-entry).
- Save-coupling school↔jail = trivial Python mapping (no RE needed). Orchestrator integration of Weg B robustness still open
  (per `HANDOVER_load-RE_2026-06-24.md` section 6).

## 1.5 Section header / topic list (RE_LADEFUNKTION)

★ BASIS-KONTEXT · ZIEL · RE-STARTPUNKTE · WEG-ENTSCHEIDUNG · SCHRITT-PLAN & STATUS (table) · STATUS (letzter Stand) ·
UMGEBUNGS-HINWEIS · TEST-RUNDE 1 · TEST-RUNDE 2 (CRASH @ 0xF3C00, Reset fehlt; LÖSUNG ASM-Trampolin) · TEST-RUNDE 3
(Trampolin v2) + BEWERTUNG/WEG · ★ TEST-RUNDE 4 (v3 voller Wrapper crasht; GameBase=0x6C0000 correction; echte Ursache) ·
ARCHITEKTUR-IDEE (Save-Swap statt Cold-Start) · FUNDE F1–F9 · STEP-6-ARTEFAKT (loadtest.lua) · TESTPROZEDUR ·
★★ RE-AUFGABE #7 COLD-LOAD vom Menü (Ziel/zu klären/DoD/NICHT im Scope/Danach/UMSETZUNG Global-Scan) · #7 MESSERGEBNISSE ·
#7 CALLER ERFASST · #7 EMPFEHLUNG · ★★ #7 TIEFEN-RE (5 Fragen) · #7 Container-Lifecycle · ★ #7 ENDBEWERTUNG ·
★★ #7 DYNAMISCH (CE+Detour) · ★★★ #7 DEFINITIVES ERGEBNIS · CE-/Debug-Umgebung Notizen · ★★★★ #7 ABSCHLUSS.

---

# 2. `HANDOVER_module_format_RE_2026-06-26.md` — AAU trigger-module binary format

## 2.1 Facts (SOLVED — format fully cracked)

- **Serializer found:** `AAUnlimited/Functions/Serialize.h` — generic `ReadData<T>`/`WriteData<T>`, all specializations inline
  in the header (no Serialize.cpp). Implemented as full codec (decode+encode) in **`module_format.py`**. (→ SOLVED banner)
- **Verification:** 466 modules × 2 worlds = **932 files**, all CLEAN PARSE + byte-exact roundtrip (`encode(decode(x))==x`).
  Batch test `_batch_test.py`. (→ SOLVED banner)

### Format / struct facts (verbatim, → SOLVED banner + §1/§2)
- **wstr** = `[u32 #chars][chars × UTF-16LE]` (no BOM, no null terminator).
- **vec** = `[u32 count][…]`.
- **int/DWORD/enum** = `u32` little-endian.
- **bool = 1 byte** (`sizeof(bool)`), NOT 4.
- **Pointer ≠ id.** `ReadData_sub(T**)` = `new T(ReadData<T>(...))` → objects serialized **inline**, not as id. (Trigger structs
  override this with their own serializers.)
- **`ParameterisedExpression` is id-dependent branched** (the @offset-88 break): reads `type:u32, id:u32`, then EXACTLY ONE:
  - id==1 (CONSTANT) → `Value`
  - id==2 (VAR) → `wstr`
  - id==3 (NAMEDCONSTANT) → `int`
  - else → `vec<ParameterisedExpression>`
- **Variable / GlobalVariable have NO serialized `id`** (struct field, but not in the file).
- **Trigger serializes ONLY** `name, events, vars, guiActions` — NOT `actions/owningCard/broken/bInitialized`
  (actions are rebuilt at runtime from guiActions). → guiActions tree is the stored one, actions is empty.
- **`Types` enum:** INVALID=0, INT=1, BOOL=2, FLOAT=3, STRING=4.
- **`Value`** = `type:u32` + payload-by-type.
- **GlobalVariable** = `type, name, defaultValue:Value, currentValue:Value, initialized:bool`.
- Exact field orders are docstrings in `module_format.py`.

### Struct layouts from AAU source (serialization order) (→ §2)
```
Module   = name:wstr · description:wstr · triggers:vec<Trigger> · globals:vec<GlobalVariable> · dependencies:vec<wstr>
Trigger  = name:wstr · events:vec<ParameterisedEvent> · vars:vec<Variable> · guiActions:vec<GUIAction*> ·
           actions:vec<ParameterisedAction> · globalVars:vec<GlobalVariable>* · owningCard:int · broken:bool · bInitialized:bool
Variable = id:DWORD · type:Types(enum) · name:wstr · defaultValue:ParameterisedExpression
ParameterisedExpression = expression:Expression*(→id) · actualParameters:vec<ParameterisedExpression> ·
           constant:Value · varName:wstr · namedConstant:NamedConstant*(→id) · varId:int
ParameterisedAction = action:Action*(→id) · actualParameters:vec<ParameterisedExpression>
GUIAction = action:ParameterisedAction · subactions:vec<GUIAction*> · parent:GUIAction*(skip)   # If/then tree
Value    = type:Types · union{ wstring* · int · float · bool }
Expression/Action (GLOBAL defs, not per-module serialized; referenced by id):
           id:DWORD · category:int · name:wstr · interactiveName:wstr · description:wstr · parameters:vec<Types> · returnType/func
```

### `Race-Human` reference token sequence (328 B; calibration anchor) (→ §1)
```
"Race-Human" "Is a human" 1 "Init" 1 6 0 1 4 "race" 4 1 4 "Human " 1 2 1 2 8 2 …(drifts here)…
```
Reading: name, desc, triggers.count=1, trigger.name="Init", events.count=1, event{id=6,params=0}, then inner struct.

### Confinement generated (→ SOLVED banner)
- `module_authoring.py` (builder lib on module_format) generates the Confinement module per §6/CONFINEMENT_MODULE_SPEC.md:
  Event 16 (Room Change) → If(ThisCard==TriggeringCard ∧ ThisCard≠PC ∧ CurrentRoom(ThisCard)≠39) → MoveNpcToRoom(ThisCard,39).
  File `Confinement` (repo-root + `school/data/override/module/`), **436 B**, decodes clean + byte-exact roundtrip.
- Verified building blocks: Event 16 · Action 20 (Make Npc Move to Room) · INT 9/10/55/97 (Triggering/This/PC/CurrentRoom) ·
  BOOL 4/8/13 (And/Equal/NotEqual).

### Key source files / URLs (→ §8)
- Repo `github.com/aa2g/AA2Unlimited`, path `AAUnlimited/Functions/Shared/Triggers/`:
  Module · Triggers · Actions · Expressions · Event · Value · NamedConstant · InfoData · Thread (.h/.cpp).
- `AAUnlimited/Files/ModuleFile.cpp` (uses ReadData/WriteData); `AAUnlimited/Files/PersistentStorage.*` (Card Storage — same serializer suspected).
- raw: `https://raw.githubusercontent.com/aa2g/AA2Unlimited/master/<path>`; listing: `https://api.github.com/repos/aa2g/AA2Unlimited/contents/<path>`.
- Tooling Python: `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe` (3.12.8).
- Active playthrough: NEW HOPE, PC = Cox Robert. Cell-room = 39 (Outside Station).

### Tools built (→ §4)
- `module_decode.py` — greedy token-dumper. `module_schema.py` — schema-driven decoder, consume-to-EOF sweep (stalled 28% of Race-Human @offset 88 before the solve).
- `module_format.py` — full proven codec. `module_authoring.py` — builder. `_batch_test.py` — 932-file roundtrip. `_expr_catalog.json` — raw id catalog.

## 2.2 [LATENT] — found but not yet used (module format)

- **[LATENT] `PersistentStorage.*` likely uses the same serializer** (Card Storage) — noted as a cross-search; not yet decoded/leveraged.
- **[LATENT] Second load fn / globalVars pointer field** in Trigger struct — present in struct but "evtl. nicht serialisiert"; codec
  treats it as not-in-file (resolved), but the *runtime* semantics (actions rebuilt via `Trigger::AddActionsFromGuiActions()`) are unused.
- **[LATENT] Status/Evolution modules** — `Set Virtue=Action32`, `Set Card Storage = Actions 24–27` declared "now trivial" to
  generate; module_authoring can build them but they're not yet generated. (→ SOLVED "NÄCHSTE PHASE" 3)
- **[LATENT] Confinement Stufe 2 (SSOT)** — read cell + inmate-flag from Card Storage (`Get Card Storage Bool/Int` = BOOL24 / INT24)
  instead of fixed 39; building blocks identified, module not yet built. (→ SOLVED "NÄCHSTE PHASE" 2)

## 2.3 [REJECTED] (module format)

- **[REJECTED: not Lua-reachable] `m_forceAction` from Lua** — probe `jail_probe.lua` confirms userdata, not a member.
  GetNpcCurrentRoom/IsPC/on.roomChange work (detection) but the SETTER is missing. (→ §0)
- **[REJECTED: none fits] No existing module pins an NPC to a location** — all 466 checked; Jailer/Chained Maiden/Toilet Police/Thot Patrol do other things. (→ §0)
- **[REJECTED: undocumented] No format docs anywhere** (GitHub wiki / anime-sharing wiki) — format lives only in source. (→ §0)
- **[REJECTED: crash-risk + unsafe addr] `g_poke` direct write** — CharInstData address from Lua unsafe. → module generator is the clean way. (→ §0)
- **[REJECTED superseded] pointer = `uint32 id` guess** — wrong; objects are serialized inline (`ReadData_sub`). (→ §1 vs SOLVED)
- **[REJECTED superseded] bool = uint32 guess** — wrong; bool = 1 byte. (→ §3 vs SOLVED)
- **[REJECTED: card corruption] raw byte-splice of modules onto cards** — corrupts cards; use AA2QtEdit (maintains `AUSS` bytes). (→ §7)

## 2.4 Open questions (module format) — mostly closed by the SOLVED banner
- Original §3 unknowns (ReadData/WriteData location, Types enum, ID values, bool width, pointer null-sentinel, guiActions-vs-actions)
  were the work-items; all resolved in the SOLVED banner except confirming PersistentStorage shares the serializer.

## 2.5 Section header / topic list (module format)
✅ SOLVED banner (2026-06-26) · 0. Warum dieser Weg · 1. Format-Erkenntnisse · 2. Struct-Layouts · 3. OFFENE UNBEKANNTE ·
4. Schon gebaute Tools · 5. Validierungs-Strategie · 6. Zielmodul "Confinement" · 7. Integration zurück ins Projekt ·
8. Schlüssel-Quelldateien · 9. Test-Module · 10. Erster konkreter Schritt.

---

# 3. `MODULE_ID_CATALOG.md` — Events / Actions / Expressions id tables

## 3.1 Facts — storage convention (→ "Wie IDs in der Datei gespeichert werden")
- **Event-ID** = enum value / 1-based registration order. `Event::FromId(id) → g_Events[id-1]`.
- **Action-ID** = 1-based position in `g_Actions`. `Action::FromId(id) → g_Actions[id-1]`.
- **Expression-ID** = 1-based index **within the return-type list**. `Expression::FromId(type,id) → g_Expressions[type][id-1]`.
  Each type list starts `1=Constant, 2=Variable, 3=Enumeration`; real functions from id 4.
  In `ParameterisedExpression` id 1/2/3 are special (Constant→Value, Var→wstr, NamedConstant→int).

### EVENTS (stored id = enum value; all events have NO params `{}`)
1 Clothes Changed · 2 Card Initialized · 3 Card Destroyed · 4 Hi Poly Model Initialized · 5 Hi Poly Model Loaded ·
6 Card Added to Class ("Init") · 7 A Period Ends · 8 Npc Answers in a Conversation · 9 Npc Starts Walking to a Room ·
10 Npc Wants to do something with no Target · 11 Npc Wants to Talk With Someone · 12 …With Someone About Someone ·
13 PC conversation state updated · 14 Pc Answers in a Conversation · 15 PC conversation line updated ·
**16 Card Changes Room** (Confinement) · 17 Key Press · 18 H Position Change · 19 After PC Response · 20 After NPC Response ·
21 HI Poly Despawn · 22 H Ends · 23 H Starts · 24 Card Expelled · 25 Conversation End · 26 Relationship Points Changed · 27 Delayed Execution.

### ACTIONS (stored id = 1-based position; params = arg types)
1 Set Variable(INVALID,INVALID) · **2 If(BOOL)** · 3 Else If(BOOL) · 4 Else() · 5 Conditional Jump(INT,BOOL) · 6 Loop() ·
7 Break If(BOOL) · 8 Continue If(BOOL) · 9 For Loop(INVALID,INT,INT) · 10 Switch Style(INT,INT) · 11 End Execution() ·
12 Add Love Points(INT,INT,INT) · 13 Add Like Points · 14 Add Dislike Points · 15 Add Hate Points · 16 Add Points(INT×4) ·
17 Conditional End Execution(BOOL) · 18 Set Npc Normal Response Success(BOOL) · 19 Set Npc Normal Response Percent(INT) ·
**20 Make Npc Move to Room(INT seat, INT room)** (Confinement) · 21 Make Npc do Action with no Target(INT,INT) ·
22 Make Npc Talk to Character(INT,INT,INT) · 23 …about someone(INT×4) ·
24 Set Card Storage Integer(INT,STRING,INT) · 25 …Float(INT,STRING,FLOAT) · 26 …String(INT,STRING,STRING) · 27 …Bool(INT,STRING,BOOL) ·
28–31 Remove Card Storage Integer/Float/String/Bool(INT,STRING) · 32 Set Virtue(INT,INT) · 33 Set Trait(INT,INT,BOOL) ·
34 Set Personality(INT,INT) · 35 Set Voice Pitch(INT,INT) · 36–38 Set Club/Club Value/Club Rank(INT,INT) ·
39–41 Set Intelligence/Value/Rank · 42–44 Set Strength/Value/Rank · 45 Set Sociability · 46 Set First Name(INT,STRING) ·
47 Set Last Name · 48 Set Sex Orientation(INT,INT) · 49 Set Description(INT,STRING) · 50 Change Player Character(INT) ·
51 Start H scene(INT,INT) · 52–53 Set Sex Experience Vaginal/Anal(INT,BOOL) · 54 Add Mood(INT,INT,INT) · 55 Replace Mood(INT×4) ·
56–58 Set Item Lover's/Friend's/Sexual(INT,STRING) · 59 Set H Compatibility(INT,INT,INT) · 60 Set NPC status(INT,INT) ·
61 Voyeur Clean Up() · 62 Set Points(INT,INT,5×FLOAT) · 63 Write Log(STRING) · 64–65 Cum Stat Vaginal/Anal(INT,INT,INT).

### EXPRESSIONS (id = 1-based per return-type; 1=Const 2=Var 3=Enum)
- **→ INT:** 4 Random Int · 5 + · 6 − · 7 / · 8 * · **9 Triggering Card()** · **10 This Card()** · 11 Npc Answer-Target ·
  12 Npc Answer-ConvID · 13 Npc Room Target · 14 Npc Action · 15 Npc Talk Target · 16 Npc Talk About · 17 Period-Starting ·
  18 Period-Ending · 19 Love Points · 20 Like Points · 22 Hate Points · 23 Float→Int · 24 Get Card Storage Int(I,S,I) ·
  25 Virtue · 26 Personality · 27 Voice Pitch · 28 Club · 29 Club Value · 30 Club Rank · 31 Intelligence · 32 Int.Value ·
  33 Int.Rank · 34 Strength · 35 Str.Value · 36 Str.Rank · 37 Sociability · 38 Partner Count · 41 Sex Orientation ·
  42 String Length · 43 First Index Of · 44 String→Int · 46 Gender · 47 Days Passed · 48 Current Day · 49 Current Period ·
  51 Current Style · 52 State · 53 Actor · **55 Player Character()** · 56 Find Seat · 64 Find Style · 68 Get NPC Status ·
  **97 Current Room(I)** · 103 Get Target · 106 Get Height · 111 Get Figure · 113 Get Breast Size · 121 Get Class Storage Int ·
  124 Real Virtue · 145 Club Type … (full: `_expr_catalog.json`).
- **→ BOOL:** **4 Logical And(B,B)** · 5 Logical Or · 6 Greater Than · 7 ≥ · **8 Equal(I,I)** · 9 ≤ · 10 Less Than · 11 Not(B) ·
  12 String-Equal · **13 Not Equal(I,I)** · 16 Is Seat Filled · 17 Is Lover · 18–23 Float comparisons · 24 Get Card Storage Bool(I,S,B) ·
  25 Trait · 35/36 Sex Exp Vaginal/Anal · 37 Has Lovers · 46 Get Class Storage Bool · 49 Has Date With.
- **→ FLOAT:** 4 Random Float · 5 + · 6 − · 7 / · 8 * · 9 Int→Float · 10 Get Card Storage Float · 11 String→Float · 13 Get Class Storage Float.
- **→ STRING:** 4 Substring · 5 Last Name · 6 First Name · **7 Get Card Storage String(I,S,S)** · **8 +(S,S)** · 9 Int→String ·
  10 Float→String · 11 Bool→String · 12 Description · 20 Full Name · 22 Get Class Storage String.

### Cross-check evidence (→ banner)
Race-Human decoded: STRING id7="Get Card Storage String", id8="+", BOOL id8="Equal", INT id9="Triggering Card", id10="This Card" — all match source.

## 3.2 [LATENT] (id catalog)
- **[LATENT] Card-Storage SSOT bridge** — Actions 24–27 (Set) + Get-expressions (INT24/BOOL24/FLOAT10/STRING7) are the
  SSOT bridge for Confinement Stufe 2 and all status modules: orchestrator/Lua writes `setCardStorage`, module reads it. Identified, not yet wired.
- **[LATENT] Class Storage** — INT121 / BOOL46 / FLOAT13 / STRING22 "Get Class Storage" — class-level storage path, unused.
- **[LATENT] Virtue/Trait/Personality/stat setters** (Actions 32–45) and Real Virtue (INT124) — full evolution-stat lever set, catalogued not used.
- **[LATENT] Delayed Execution event (27)** and **For Loop / Conditional Jump (9/5)** — control-flow primitives available for richer modules.

## 3.3 [REJECTED] — none stated in this doc.

## 3.4 Open questions (id catalog)
- Full expression tables (all ids incl. gaps) reproducible from `Expressions.cpp` via the `module_authoring.py` companion script;
  catalog here only bolds status/evolution-relevant ids.

## 3.5 Section header / topic list (id catalog)
Wie IDs in der Datei gespeichert werden · EVENTS · ACTIONS · EXPRESSIONS (→INT / →BOOL / →FLOAT / →STRING).

---

# 4. `CONFINEMENT_MODULE_SPEC.md` — Confinement module spec

## 4.1 Facts (→ Verifizierte Trigger-Bausteine + Stufe 1/2)
- Holds NPCs on one map node (jail cell). Reactive (Jailer principle), not preventive — no preventive lever exists in the
  engine (AI movement = undocumented arrays; gender "gate" is soft). Pure Lua eject impossible (`m_forceAction` not Lua-reachable).
- Verified trigger building blocks (role | editor name | internal):
  - Event | **Room Change** | room-change event
  - NPC current room | **"Npc Current Room"** (param seat) | `GetNpcCurrentRoom(seat)` → int
  - Player seat | **"PC"** / Get PC | `GetPC()` → seat (−1 if none)
  - This card | **This Card** | `GetThisCard()` → seat
  - Triggering card | **Triggering Card** | `GetTriggeringCard()` → seat
  - Action (send back) | **"Make Npc Move to Room"** (seat, room) | `NpcMoveRoom(seat, roomId)`
- **`NpcMoveRoom` internal:** sets `m_forceAction.movementType=2; roomTarget=roomId`. (→ HANDOVER module §6 cross-ref)
- **CELL = 39** (Outside Station — the star-node / fixed origin bottom-right). To verify: stand PC on the node, check
  `jail/_orch_probe.flag` line `Cox Robert ... room=<X>`; if X≠39, X is the real cell index.

### Stufe 1 trigger (fixed cell)
```
EVENT:  Room Change
CONDITIONS (all AND):
  1. This Card == Triggering Card        # only react when I moved
  2. This Card != PC                     # GetThisCard() != GetPC() → NPCs only
  3. Npc Current Room(This Card) != CELL # I'm outside the cell
ACTIONS:
  1. Make Npc Move to Room(This Card, CELL)
```
- Self-limiting: once back in CELL, condition 3 false → no re-fire. Idempotent if it fires mid-return. Covers the flee case
  automatically (any reason for leaving). Corruption values (virtue=0) dampen shock-flee.

### Stufe 2 (SSOT-driven, later)
```
CONDITIONS:
  1. This Card == Triggering Card
  2. This Card != PC
  3. CardStorage(This Card,"in_jail") == 1
  4. Npc Current Room(This Card) != CardStorage(This Card,"cell")
ACTIONS:
  1. Make Npc Move to Room(This Card, CardStorage(This Card,"cell"))
```
- Per-NPC configurable, storage-gated (module preinstalled on all cards, active only when `in_jail=1`), world/future-proof.
  Bridge: orchestrator writes a flag → small Lua mod applies it via `setCardStorage` (`in_jail`, `cell`). Multiple allowed
  rooms = list in storage + "Room in list" condition.

## 4.2 [LATENT] (Confinement spec)
- **[LATENT] Stufe 2 storage-gated module** — designed in full but not built; the generic SSOT confinement path. Building
  blocks all catalogued (Card Storage get/set ids).
- **[LATENT] "returning=1" Card-Storage flag** — optional cleaner loop-guard condition, mentioned but unused.
- **[LATENT] Multiple-allowed-rooms list in storage** — "Room in list" condition variant, sketched not implemented.

## 4.3 [REJECTED] (Confinement spec)
- **[REJECTED: no engine lever] Preventive movement block** — AI movement = undocumented arrays; gender gate is a soft
  reaction, not a hard gate. → reactive Jailer approach instead.
- **[REJECTED: not Lua-reachable] Pure Lua eject** — `m_forceAction` not Lua-reachable (probe confirmed) → trigger system is the stable way.

## 4.4 Open questions (Confinement spec)
- Confirm cell-room index (default 39, verify via `jail/_orch_probe.flag`).
- Confirm editor dropdown display names (identify by function if names differ slightly).

## 4.5 Section header / topic list (Confinement spec)
Intro · Verifizierte Trigger-Bausteine · STUFE 1 — MVP · STUFE 2 — generisch + SSOT-getrieben · Was DU jetzt brauchst.

---

# CORPUS 2/4 — HANDOVERS (detailed extraction)

# MASTER BLUEPRINT — Source Extraction from Handover Docs

> Preservation pass over all 10 handover docs in `D:\Games\MWA2`, newest first.
> Goal: nothing-lost reference. Every fact, every LATENT (discovered-but-unused) finding,
> every REJECTED approach, every open question. Provenance cited as (file → section).

---

# 1. HANDOVER_reroute_mwaid_2026-06-26.md — Module Reroute Hook + stable mwa_id + SSOT re-key

## Headers / topics
- ★★ ARCHITEKTUR-KORREKTUR (Nutzer, Ende der Session) — Karten werden NIE verändert
- 0. TL;DR — der große Sprung dieser Session
- 1. Was BEWIESEN funktioniert (in-game verifiziert)
- 2. HARTE FAKTEN (alle live verifiziert; AAUnlimitedDll.dll RE)
- 3. STATUS — Phasen 1–3 ALLE FERTIG; NÄCHSTER SCHRITT: voller Karten-Tag-Bootstrap
- 4. Diese Session geänderte/neue Dateien
- 5. OFFENE PUNKTE / Warnungen
- 6. FAKTEN / Umgebung

## Facts
- **AAUnlimitedDll.dll** = RELEASE x86 build, ImageBase `0x10000000`, relocated. DLL base obtained via `GetModuleHandleA("AAUnlimitedDll.dll")`. Native calls via `proc_invoke(addr, this, ...args)`.
- **RVAs (from `.pdb` via scratchpad `pdb_rva.py`):**
  - `AAUCardData::UpdateModules` = **0x154CF0** (`__thiscall void(void)`). Hooked via `mod/memory.lua`'s `hook_func`. Reads/writes the live module + global list of each card on load, **VOR `InitOnLoad`** (so triggers get activated).
  - `AddModule(wchar_t*)` = **0x14CEC0** (returns `bool`; needs FULL path: `GetAAPlayPath().."data\\override\\module\\<name>"`; bool in AL → `(eax&0xff)~=0`).
  - `RemoveModule(int)` = **0x14D290**.
- **AAUCardData layout** (wstring size = 24 bytes):
  - `m_globalVars` vec @ **0x24**
  - `m_modules` vec @ **0x3C**
  - `m_cardStorage` map @ **0x48**
- **sizeof(Module) = 84**: name@0, desc@24, triggers@48, globals@60, deps@72.
- **sizeof(GlobalVariable) = 0x34**: id@0, type@4, name@8, defaultValue@0x20, currentValue@0x28 (type@0x28, iVal@0x2C), initialized@0x30.
- **wstring read convention:** size@+16, res(reserved)@+20, inline iff res<8 else ptr@+0.
- **aaUd on-disk tags (byte-reversed):** TrGv = `vGrT`, TrMd = `dMrT`, TrAt = `tArT`. Member = `[tag][serialized]`, **NO length prefix**.
- **GlobalVariable on-disk** = `[u32 type][wstr name][Value default][Value current][u8 init]`. `Value` = `[u32 type][INT i32 / BOOL u8 / FLOAT f32 / STRING wstr]`. **`id` is NOT serialized.**
- **Insert trick:** splice serialized element directly after the vector Count + increment Count (no parsing needed), then fix PNG/sav chunk length + CRC32.
- **.sav embedded cards** are real PNGs with an aaUd chunk; **NO outer length field** → self-delimiting up to IEND.
- AAU's own aaUd CRCs are invalid anyway (engine parses by length) — "bad CRC" is normal.
- **Stable `mwa_id`** = INT **Global Variable** named `"mwa_id"` on the card (rename/editor/transfer-resistant). Written offline via `card_globals.py` (.png) or scratchpad `sav_tag_id.py` (.sav-embedded cards). Round-trip proven: **Shimizu=1001, Takagi=1002, Luka=1003**.
- **Reroute hook proven end-to-end:** Stage Luka (card not splice-able) confined ONLY via hook `AddModule` → walked to station (room 39). Read+write+activation proven.
- **SSOT re-keyed to mwa_id** in `memory.db` + `playthrough_db.py`: `ensure_mwa_id`/`mwa_id_of`/`name_of`/`rename_char`, `confined_mwa()` → `{id:cell}`. Rename resilience proven.
- **Phase 3:** `orchestrator.write_reroute()` writes `_orch_reroute.flag` (`<mwa_id>\t<mods>`, both worlds) from resolver output. `module_reroute.lua` v3 reads card's `mwa_id` → looks up → `AddModule` (additive). Log proof: `desired={Confinement} applied={Confinement}`.
- **Environment:** Python `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe`. Japanese paths need `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` (cp1252 console crashes otherwise).
- Playthrough **NEW HOPE** (`_playthroughs\NEW HOPE学園1年1組\memory.db`). PC = Cox Robert (mwa_id 1006). Inmates: Shimizu Airi (1001), Takagi Saya (1002), Stage Luka (1003). Cell = room 39.
- **Mod code is read only at PROCESS START** → for new mod code, fully restart jail (not just reload).
- Hook debug log: `jail/_orch_reroute_debug.flag` (rewritten per class-load).
- Confinement module is Stage-1 (flagless, "NPC≠PC, room≠39 → MoveToRoom 39").

## [LATENT] unused / abandoned / for-later findings
- **[LATENT] `RemoveModule(int)` = 0x14D290** — discovered, NOT yet used. Intended for "clear+replace" path: `RemoveModule(0)` loop + `AddModule` = "ignore card modules entirely" (ID-Global preserved, orthogonal). Listed as optional next step (b).
- **[LATENT] Full card-tag bootstrap is the main gap.** Only the 3 inmates in the jail `.sav` are correctly tagged; PC + students have **placeholder IDs 1900-1910** → don't match the flag (PC gets no Sex Addict despite being in flag). TODO: tag ALL 34 chars with real DB `mwa_id` (school cards/.sav + replace jail .sav placeholders). `mwa_id` per char = `pdb.mwa_id_of`. Identify .sav blocks by module-signature (like `sav_tag_id.py`) or names from `.json` sidecar.
- **[LATENT] Reroute mod is jail-side only.** For school/evolution it must also be hooked in there later.
- **[LATENT] Flag-gated Stage-2 confinement** still pending (Stage-1 flagless is what's live).
- **[LATENT] Scratchpad tools to possibly pull into repo:** `pdb_rva.py`, `sav_splice.py` (module splice .sav), `sav_tag_id.py` (mwa_id in .sav), `migrate_mwaid.py` (DB migration), `install_confine.py`.
- **[LATENT] `card_edit.py`** (.png add/remove module) now redundant for confinement (hook does it) but retained.

## [REJECTED] approaches
- **[REJECTED: cards must stay shareable]** Stamping ANYTHING onto cards (mwa_id global on cards, Confinement splice into .sav/.png) is WRONG. Cards are pure shareable BASE data; any bit-change breaks the card for non-mod users. The "mwa_id-on-card" persistence described in §1/§2 is **VERWORFEN (discarded)**. Base `.png`s already reset. ✅ CORRECT: reroute hook changes module list **in-memory on load only** (card file untouched); SSOT (memory.db, keyed on mwa_id) is external. NOTE: the RE facts in §2 (RVAs, layout, native calls) still hold — only the on-card persistence is rejected.
- **[REJECTED: redundant]** Confinement module splices in Shimizu/Takagi `.sav`+`.png` are now superfluous (hook does it). Optionally reset to pristine (backups exist) so cards stay untouched (architectural ideal).

## Open questions
- Verify orchestrator live-flag fires on school-save (`write_reroute`).
- Calibrate resolver thresholds.
- Whether to reset redundant confinement splices to pristine (backups `_backup/*.preid.*`).

## Corrected identity model — "active roster" (architectural anchor)
- Every save starts EMPTY; roster is BUILT via `AddCard` from base `.png`s (`jail_intake` does this: reads `_orch_jail_inmates.flag` = `name\tcardfile\tgender`).
- Because WE build the roster, we know per card: **base cardfile → (SSOT) mwa_id → modules/experiences** — without reading id from card, without seat (seat = transient handle only).
- Same base card in different playthroughs = a different evolved char. Char leaves roster → data frozen in DB (by id); card returns → old experiences + new. `mwa_id` stays internal SSOT key, **linked from cardfile**, not stamped.
- Next build target: (1) introduce `chars.cardfile` as link; (2) orchestrator emits per inmate `cardfile→mwa_id→module-list`; (3) `jail_intake` sets context (cardfile/id/module) BEFORE each `AddCard`, hook reads this context (same Lua process, NO card stamp) and applies modules in-memory; (4) empty-start saves (user tests with fresh save + test chars). Ref: [[char-id-one-ssot]].

---

# 2. HANDOVER_confinement_2026-06-26.md — Confinement + SSOT module control

## Headers / topics
- 0. TL;DR — wo wir feststecken
- 1. Das KERN-PROBLEM (Confinement module not firing in-game)
- 2. Was BEWIESEN funktioniert (nicht nochmal anfassen)
- 3. ★ ARCHITEKTUR-REGELN (vom Nutzer hart korrigiert)
- 4. Diese Session gebaut/geändert (Dateien)
- 5. WEITERE OFFENE PUNKTE
- 6. FAKTEN / Umgebung

## Facts
- Full Python/Lua pipeline works: SSOT → char_state → apply_state calls `setCardStorage` (flag-proven).
- **Engine action "Set/Get Card Storage"** (Actions.cpp) uses `inst->m_cardData.GetCardStorage()[key]`.
- Lua `setCardStorage` (`triggers_supplemental.lua:309`) writes into **Class Storage** under key `"<seat> <forename> <surname>"` — a DIFFERENT location than engine Card Storage. So the module reading engine Card Storage never sees the flags.
- **No documented Lua API for engine Card Storage** (lua-cruft wiki). Channels: raw memory (`poke`), OR **Class Storage as shared channel** (Lua `set_class_key` + module expression "Get Class Storage Bool/Int" = BOOL46 / INT121, char-name as key), OR undocumented init.lua API.
- **Verified module-authoring IDs:** Event16 RoomChange / Event6 CardAdded · Action20 NpcMoveRoom / Action2 If / Action24-27 SetCardStorage · Expr INT9/10/55/97, BOOL4/8/13/24, INT24 GetCardStorageInt.
- **Card-storage convention:** `@b:` = Bool, `@i:` = Int (in cardstorage strings, e.g. `@b:confined=1;@i:cell=39`).
- `JAIL_CELL = 39`.
- **apply_state v1 proven:** `virtue=0` on live char, read-back verified.
- **Module-format codec (`module_format.py`):** 932 files byte-exact decode+encode.
- **SSOT→Card-Storage bridge proven (Python/Lua side):** `confine` → `memory.db` → resolver → `char_state.flag` with `@b:confined=1;@i:cell=39` → apply_state calls `setCardStorage` (apply_debug shows `applied: Shimizu Airi{@b:confined=1;@i:cell=39}`). Bridge is NOT the problem — only its target (cause A).
- **Auto-Confine:** Orchestrator confines all jail-residents (Shimizu Airi, Stage Luka, Takagi Saya) to 39.
- **Confinement module** generated (Stage-1 + Init, 516 B in this doc's build). jail-only. *(NB: the byte-exact final
  Confinement module is **436 B** per HANDOVER_module_format_RE / CONFINEMENT_SPEC — the 516 B figure is this earlier
  Stage-1+Init build; treat 436 B as current.)*
- **PPeX is irrelevant** for confinement (streams assets only, never touches Card Storage / logic).
- **`AA2QtEdit.exe`** = standalone card editor (maintains AUSS safely; no PPeX needed).
- AAU source via WebFetch (raw.githubusercontent.com); `gh` missing in Bash PATH.
- Cell room 39 = "Outside Station".

## [LATENT] unused / for-later findings
- **[LATENT] Class Storage as shared channel** — proposed fix for cause A (BOOL46 / INT121 "Get Class Storage Bool/Int", char-name as key). Not yet built. This is the route to make flag-gated modules read SSOT flags.
- **[LATENT] Stage-2 flag-gated confinement** (`build_confinement_gated()`) reads Card Storage `confined`/`cell` — built but blocked by cause A (storage location mismatch). To revisit once "modules must be installed" is resolved.
- **[LATENT] `jail_phase.lua`** (time-phase: steers Club(7)→End(8)) — built but does NOT fire in-game (debug-flag empty). Separate open topic: day doesn't start at the right in-game time.
- **[LATENT] `jail_probe.lua`** — read-only recon (rooms + m_forceAction reachability). DEV, can be removed.
- **[LATENT] `debug_force.lua`** (school) — set engine-H stats via flag (test accelerator).
- **[LATENT] `debug_tool.py`** CLI (`run_debug.bat`): `dump/show/set/race/racexp/resolve/force/confine/unconfine`.
- **[LATENT] Status/evolution modules** (Prisoner/broken/trainer) need the Card-Storage bridge (cause A) once module-install question is settled.
- **[LATENT] resolver MODULE_EFFECTS = placeholders** — thresholds/effects need calibration.

## [REJECTED] approaches / dead ends
- **[REJECTED: wrong location]** Writing confine flags to Class Storage under `"<seat> name"` while the module reads engine Card Storage — different stores, module never sees flags. (This is cause A; not "rejected" so much as identified-as-broken.)
- **[REJECTED: redundant]** A separate `_orch_confine.flag` — removed; now `char_confine` table in the single DB. (User architecture rule: one memory.db, no world-specific redundant DBs/flags.)
- Separate confine-flag logic in apply_state — removed again (folded into the `@b:`/`@i:` injection).

## ★ THE CORE PROBLEM (open, primary blocker for this doc)
- **Confinement module (`jail/data/override/module/Confinement`, our generated one) does NOT act in-game.** NPCs walk free, none goes to cell (room 39). Two causes isolated:
  - **(A) Card-Storage incompatibility** (affects flag-gated Stage-2): store-location mismatch above.
  - **(B) Module doesn't load** (affects EVEN the flagless Stage-1): Stage-1 module ("NPC≠PC, room≠39 → MoveNpcToRoom(39)") also doesn't fire → rules out (A) as sole cause. **Strongest suspicion: a module in `data/override/module/` only fires if it is "In Use" on at least one card.** "All modules always load" applies to those already installed on cards, NOT to our new one. Adding Init-Trigger (Event 6 = Card Added) — which all real modules have — still didn't fire.
  - **★ NEXT STEP (open, user to execute):** push Confinement via AA2QtEdit onto ONE jail-NPC card "In Use" → save → reload jail. Does she go to room 39?
    - ✅ → modules must be installed. Real path = pre-install once on all cards, then SSOT flags drive (+ solve cause A for flag version).
    - ❌ → module is structurally not loadable (despite codec roundtrip) → dig there (Init/Globals/format).
  - **NOTE:** This whole blocker was later SOLVED by the reroute hook (next doc / dated same day "spät²") which calls `AddModule` natively in-memory — bypassing the "must be installed on card" question entirely.

## Architecture rules (user-enforced)
- **char_id-based, NEVER seat.** Identity = normalized name. NPC has different seats in school/jail. Seat = runtime handle only. (Notes §2.4d.)
- **ONE `memory.db` per playthrough**, shared by all worlds. No world-specific redundant DBs/flags.
- **Modules: pre-installed on cards + storage-gated (§4.6). SSOT distributes ONLY the flags.** Card module-list is carrier; SSOT is truth.
- **jail = ALL inmates confined** (definition of jail). Not selective. jail roster = inmates + PC only.

## Files built this session
- `module_authoring.py` — builder on module_format. `build_confinement(cell)` = Stage-1; `build_confinement_gated()` = Stage-2.
- `playthrough_db.py` — `char_confine(char_id,cell,ts)` table + `set_confine`/`clear_confine`/`all_confined`/`confine_of`.
- `resolver.py` — `resolve_char` adds `("Confinement","confine")` if confined; `cardstorage_string(con, char_id)`.
- `orchestrator.py` — `JAIL_CELL=39`; `transfer_sync` auto-confines all jail-residents + releases non-residents.
- `*/AAUnlimited/mod/apply_state.lua` (both worlds, identical) — inject also sets `@b:`/`@i:` fields via `setCardStorage`.
- `run_orchestrator.bat`→Python312 + `run_ui`→`run_headless` fallback (bat-crash was Tcl).

---

# 3. HANDOVER_module_format_RE_2026-06-26.md — AAU module binary format RE

## Headers / topics
- ✅ SOLVED banner (format fully cracked)
- 0. Warum dieser Weg (context)
- 1. Format-Erkenntnisse (gesichert)
- 2. Struct-Layouts (aus AAU-Quelle)
- 3. OFFENE UNBEKANNTE (original, mostly resolved)
- 4. Schon gebaute Tools
- 5. Validierungs-Strategie
- 6. Zielmodul "Confinement"
- 7. Integration zurück ins Projekt
- 8. Schlüssel-Quelldateien (AAU GitHub)
- 9. Test-Module (lokal)
- 10. Erster konkreter Schritt der RE-Session

## Facts (SOLVED — format fully cracked)
- **Serializer found: `AAUnlimited/Functions/Serialize.h`** — generic `ReadData<T>`/`WriteData<T>`, all specializations INLINE in the header (no Serialize.cpp). Entire format exactly known, implemented in `module_format.py` as a full codec (decode + encode).
- **Verification:** 466 modules × 2 worlds = **932 files**, all CLEAN PARSE + byte-exact roundtrip (`encode(decode(x)) == x`). Batch test: `_batch_test.py`.
- **Pointer ≠ id.** `ReadData_sub(T**)` = `new T(ReadData<T>(...))` → objects serialized INLINE, not as id. (Trigger structs have their own serializers.)
- **`ParameterisedExpression` is id-dependent branched** (the break @offset 88): reads `type:u32, id:u32`, then EXACTLY ONE of:
  - id==1 (CONSTANT) → `Value`
  - id==2 (VAR) → `wstr`
  - id==3 (NAMEDCONSTANT) → `int`
  - else → `vec<PExpr>`
- **`bool` = 1 byte** (`sizeof(bool)`), not 4.
- **Variable/GlobalVariable have NO serialized `id`** (struct field, but not in file).
- **Trigger serializes ONLY** `name, events, vars, guiActions` — NOT `actions/owningCard/broken/bInitialized` (actions built at runtime from guiActions). guiActions tree is what's saved; actions is empty.
- **`Types` enum:** INVALID=0, INT=1, BOOL=2, FLOAT=3, STRING=4.
- **`Value`** = `type:u32` + payload after type.
- **GlobalVariable** = `type, name, defaultValue:Value, currentValue:Value, initialized:bool`.
- **wstr** = `[u32 #chars][chars × UTF-16LE]`. **vec** = `[u32 count][…]`.
- Exact field orders are docstring in `module_format.py`.
- **ID CATALOG DONE:** `MODULE_ID_CATALOG.md` — all Events (27), Actions (65), Expressions (per type, full) with IDs↔names↔param-types, extracted from `Event.cpp`/`Actions.cpp`/`Expressions.cpp`, checked against real modules. Raw data: `_expr_catalog.json`.
  - **Storage convention:** Event-id = enum value · Action-id = 1-based position · Expression-id = 1-based index **per return type** (each type list starts 1=Const / 2=Var / 3=Enum).
- **CONFINEMENT GENERATED:** `module_authoring.py` builds it exactly per §6 / `CONFINEMENT_MODULE_SPEC.md`: Event 16 (Room Change) → If(ThisCard==TriggeringCard ∧ ThisCard≠PC ∧ CurrentRoom(ThisCard)≠39) → MoveNpcToRoom(ThisCard,39). Lives at `Confinement` (repo root + `school/data/override/module/`), 436 B, decodes clean + roundtrips byte-exact.
  - **Verified building blocks:** Event 16 · Action 20 (Make Npc Move to Room) · INT 9/10/55/97 (Triggering/This/PC/CurrentRoom) · BOOL 4/8/13 (And/Equal/NotEqual).
- **`Race-Human`** = 328 B file. Token sequence reference (for calibrating):
  `"Race-Human" "Is a human" 1 "Init" 1 6 0 1 4 "race" 4 1 4 "Human " 1 2 1 2 8 2 …`
  Reading: name, desc, triggers.count=1, trigger.name="Init", events.count=1, event{id=6,params=0}.
- **Module struct** = name:wstr · description:wstr · triggers:vec<Trigger> · globals:vec<GlobalVariable> · dependencies:vec<wstr>
- **Trigger struct** = name:wstr · events:vec<ParameterisedEvent> · vars:vec<Variable> · guiActions:vec<GUIAction*> · actions:vec<ParameterisedAction> · globalVars:vec<GlobalVariable>* · owningCard:int · broken:bool · bInitialized:bool
- **Variable** = id:DWORD · type:Types(enum) · name:wstr · defaultValue:ParameterisedExpression
- **ParameterisedExpression** = expression:Expression*(→id) · actualParameters:vec<ParameterisedExpression> · constant:Value · varName:wstr · namedConstant:NamedConstant*(→id) · varId:int
- **ParameterisedAction** = action:Action*(→id) · actualParameters:vec<ParameterisedExpression>
- **GUIAction** = action:ParameterisedAction · subactions:vec<GUIAction*> · parent:GUIAction*(skip) — the If/then tree.
- **Value** = type:Types · union{ wstring* · int · float · bool }.
- **Expression/Action GLOBAL defs** (NOT serialized per module; referenced by id only): id:DWORD · category:int · name:wstr · interactiveName:wstr · description:wstr · parameters:vec<Types> · returnType/func.
- **NpcMoveRoom** (Actions.cpp) sets `m_forceAction.movementType=2; roomTarget=roomId`.
- Building blocks verified: `NpcMoveRoom`, `GetNpcCurrentRoom(seat)`, `GetPC()`, `GetThisCard()`. Room 39 = Outside Station (verified).
- **Key source files (raw URLs):** `github.com/aa2g/AA2Unlimited → AAUnlimited/Functions/Shared/Triggers/` (Module.h/.cpp, Triggers.h/.cpp, Actions.h/.cpp, Expressions.h/.cpp, Event.h/.cpp, Value.h/.cpp, NamedConstant.h/.cpp, InfoData.h/.cpp, Thread.h/.cpp); `AAUnlimited/Files/ModuleFile.cpp` (uses ReadData/WriteData); `AAUnlimited/Files/PersistentStorage.*` (may share serializer — Card Storage cross-search). Raw form: `https://raw.githubusercontent.com/aa2g/AA2Unlimited/master/<path>`. Dir listing: `https://api.github.com/repos/aa2g/AA2Unlimited/contents/<path>`.

## [LATENT] unused / for-later findings
- **[LATENT] PersistentStorage.* may use the same serializer** as Card Storage → cross-search suggested, not done. Relevant to the Card-Storage bridge problem (cause A from doc 2).
- **[LATENT] Status/evolution module generation now trivial:** Set Virtue = Action32, Set Card Storage = 24–27. Listed as next phase, not yet built. (Prisoner/broken/trainer/Heimkehrer.)
- **[LATENT] Confinement Stage 2** (SSOT): read Card Storage (Get Card Storage Bool/Int = BOOL24 / INT24) instead of fixed 39.
- **[LATENT] `module_decode.py`** — greedy token dumper (shows strings + uint32s roughly). Superseded by codec but exists.
- **[LATENT] `module_schema.py`** — schema-driven decoder, "consume-to-EOF" sweep method; reached 28% of Race-Human (broke @offset 88). Superseded by the solved codec.
- **[LATENT] Editor as ground truth:** drop generated module → open in AAU Trigger Editor → does it render the intended logic? Roundtrip `decode(encode(decode(x)))==x`. (Validation method available.)
- **[LATENT] Test modules ladder (local, small→large):** `Race-Human` (328 B, Init+Variable only — calibration); `Race-Demon` (diff partner); `Begone Thot` (3992 B — Events + Actions; matches user screenshot "slap detect"); `Blackmailer` (complex nested If/then — screenshot "Blackmailer::PC").

## [REJECTED] approaches
- **[REJECTED: not reachable from Lua]** `m_forceAction` is NOT reachable from Lua (probe `jail_probe.lua` confirms: userdata, no member). `GetNpcCurrentRoom`/`IsPC`/`on.roomChange` work (detection), only the SETTER is missing. → This forced the module-generator route.
- **[REJECTED: no ready module]** None of the 466 modules holds an NPC at one location (Jailer = roles/roof/temporary; Chained Maiden / Toilet Police / Thot Patrol = something else). Checked.
- **[REJECTED: no format docs]** Neither GitHub wiki nor anime-sharing wiki documents the format (only a download index). Format lives only in source.
- **[REJECTED: crash risk]** `g_poke` would work but crash-risk + CharInstData address from Lua uncertain. → module generator (format RE) is the only clean reusable path.

## Open questions (mostly resolved by the SOLVED banner)
- Original §3 unknowns (find ReadData/WriteData, Types enum, Event/Action/Expression id values, bool width, pointer null-sentinel, guiActions-tree vs actions-flat) — ALL resolved per SOLVED banner.
- Open: in-game test of generated Confinement via AA2QtEdit (carries into doc 2's blocker).

---

# 4. HANDOVER_evolution_2026-06-25.md — Evolution pipeline + global pool

## Headers / topics
- 0. TL;DR — der große Pivot
- 1. Die Architektur (globaler Pool)
- 2. Diese Session gebaut (Dateien)
- 3. ★ SACKGASSE: Module auf Karten schreiben (NICHT wiederholen)
- 4. Aktueller Test-Stand + Verifikation
- 5. OFFEN / nächste Schritte
- 6. FAKTEN / Umgebung

## Facts
- **Architecture pivot:** away from "write modules onto card" (dead end, corrupts cards) → **GLOBAL POOL**: DB is truth, evolution computed centrally (resolver), applied at runtime to live chars, card never written.
- **Pipeline (proven viable):**
  `Engine events → DBs (char_activity · char_rels · char_race_xp) → resolver.py (EVOLUTION_MAP rules) → char_state ("active modules per char") → orchestrator write_char_state → _orch_char_state.flag (BOTH worlds) → apply_state.lua → sets virtue/stats on LIVE char (card untouched)`
- **Why it works:** AAU trigger system is **global** (`TriggerEventDistributor`: `loc_triggers`, run per event independent of "owner"). Thesis: behavior emerges from VALUES via AA2 engine → apply values from SSOT (proven `inject_self` pattern) covers the majority.
- **In-game proof captured:** real H-activity (Kuroda) → DB → resolver decided `Kuroda → Corruption` → written to char_state. `_orch_activity_snapshot.flag` had Kuroda (climax 11, cumIn*…). `_orch_char_state.flag` had `Kuroda Katsuki → Corruption (virtue=0)`. Resolver verified.
- **apply_state gate-bug FIXED** (was gated on roster, now gated on actually-applicable content → re-applies on state change without roster change).
- **`module_format.py` codec:** 932 files byte-exact (consistent with doc 3).
- **Threshold `SEX_CORRUPT=15`** (was briefly 1 for test, reset). Kuroda sum ~17 ≥ 15 → triggers.
- **Resolver axes:** sexual axis Corruption→Sex Addict; race axis via `race_attitude`. `MODULE_EFFECTS`/`effects_string` = module→value effect.
- **DB tables (`playthrough_db.py`, all unit-tested):** `char_activity` (cumulative H counters); `char_race`+`char_race_xp` (race axis, escalation ladder via `race_attitude`); `char_state` (resolver output: active modules per char) + `replace_char_state`/`char_state_of`/`all_char_ids_with_data`.
- **`activity_snapshot.lua`** (school) — snapshots cumulative H-counters per char (climax, totalH, cumIn*, riskyCum…, summed over partners) → `_orch_activity_snapshot.flag`.
- **`apply_state.lua`** (school) — the global apply-mod. Reads `_orch_char_state.flag`, sets values per present char (pattern `jail_intake`/`inject_self`).
- **`run_edit.py` + `run_edit.bat`** — start AA2Edit (char-creator) with PPeX environment (AA2Edit needs running PPeX server; standalone crashes). Starts PPeX + editor, stops cleanly. Works.
- **`debug_tool.py` + `run_debug.bat`** — finds active DB automatically (`school/_orch_save.flag` → `_playthroughs/<key>/memory.db`). Commands: `dump`, `show <name>`, `set <name> <metric> <value>`, `race <name> <race>`, `racexp <name> <other_race> <pos> <neg>`, `resolve`, `force <name> <metric> <value>`. UTF-8 streams.
- **Engine setter (flag-driven):** `debug_tool.py force` writes `school/_orch_force_activity.flag`; `debug_force.lua` (school-forcedconfig, DEV-only) polls it (iup-timer 700ms, pattern apply_state), sets present char's engine counter via `m_characterStatus:m_<metric>(towards,value)` (setter form proven in `triggers_supplemental.lua` Z.443-450), consumes the line (one-shot). Semantics: counters are per-partner, snapshot sums → mod nulls other partner-slots and puts full value on one → **sum = value** (predictable, destroys per-partner history = ok for debug).
- **Environment:** Python312 = `C:\Users\Henta\AppData\Local\Programs\Python\Python312\python.exe` (3.12.8). `py`/`python` in Bash PATH = broken Windows-Store stub. Orchestrator runs on `py`/3.14 (stdlib+ctypes).
- **`D:\Games\AA2MiniPPX` = unchanged pre-mod backup → READ ONLY, never write** (memory saved).
- **AAU source:** github.com/aa2g/AA2Unlimited (`AAUCardData.cpp`, `Serialize.h`, `Shared/TriggerEventDistributor.cpp`, `Shared/Triggers/*`).
- **Editors:** `AA2QtEdit.exe` = dedicated card/data editor (standalone, reads aaUd directly, no PPeX). `AA2Edit.exe` = char-creator with 3D (needs PPeX + AAU runtime → via `run_edit`).
- **`run_orchestrator.bat` crash FIXED.** Cause: bat resolved `python`/`py` → Python314, whose tkinter can't find `init.tcl` (Tcl under `Python314\tcl\…`, searched `Python314\lib\…`) → `tk.Tk()` (run_ui) throws `TclError` → the `finally: cleanup()` tore down all worlds. Direct start worked because it used Python312. Two fixes: (a) `run_orchestrator.bat` → Python312 explicitly; (b) `run_ui` falls back to `run_headless` on `TclError` (worlds stay up, switch via console-Enter) instead of tearing down — `jail_ready_for_current`/`switch_world` moved to module level.

## ★ DEAD END (documented, DO NOT REPEAT) — Module on cards via byte-splice
- **[REJECTED: corrupts cards — AUSS coupling]** `card_edit.py` READS modules cleanly (PNG aaUd chunk → `dMrT` member = `[count][self-delimiting modules]`; a card element is **byte-identical to the definition file** `data/override/module/<name>`). Reader = solid. **Writing via byte-splice (append definition file + bump count + fix CRC) CORRUPTS the card.** Reason: AAU couples module state with the **`AUSS` member** (AAU char data). Adding Corruption changed 5 bytes there (byte 161 = Style-Count=4; + 4 style slots in the step-92 array) that "Update Modules" in the editor maintains but a splice doesn't. **Even a style-free module (Blackmailer) wrecked the card.** Symptom: AAU discards the whole aaUd → no tan/modules, black render fallback. **Proven** by diff "game-generated vs spliced 3-module card" (only 5 AUSS bytes differ). Source confirms format (`AAUCardData.cpp`/`Serialize.h`), but AUSS is the killer.
- → Surgical module-writing is DEAD. The global pool (runtime apply) bypasses it. `card_edit.py` remains useful as a READER.

## [LATENT] unused / for-later findings
- **[LATENT] `char_race`/`char_race_xp` DB layer built but capture NOT wired.** Race axis has NO live capture — `debug_tool.py race`/`racexp` is the only way to test it. TODO: populate `char_race` (race from card-modules, externally at day boundary — modules not Lua-readable) + race-xp capture (dominance→negative via master_slave, loving H→positive).
- **[LATENT] Race subsystem 24×5 + HOSTILE ladder** documented in `MODULE_CATEGORIZATION.md` (race_attitude escalation).
- **[LATENT] `activity_snapshot` jail-side?** — currently school-only; needed if jail-H should contribute to evolution. Open decision.
- **[LATENT] debug_force.lua in-game UNTESTED** (no Lua compiler locally) — CLI side tested only.
- **[LATENT] Value-effect model (`MODULE_EFFECTS`)** = placeholders (virtue=0). Calibration pending.
- **[LATENT] Loneliness rule** (resolver) — needs world-state/presence (co-presence isolation). Not built.
- **[LATENT] Docs produced:** `MOD_CARTOGRAPHY.md`, `MODULE_CATEGORIZATION.md` (466 modules + `developable` + race-subsystem + HOSTILE ladder), `EVOLUTION_MAP.md`.

## Open questions / pending verification
- Apply after restart: `_orch_apply_debug.flag` should show `applied: Kuroda Katsuki{virtue=0}`, Kuroda's virtue=0, card untouched. (Gate-fix verification — formality.)
- `_orch_apply_debug.flag` was EMPTY → apply_state hadn't applied (gate-bug). Fixed, restart verification pending.

## Done items
- ✅ jail-mirror (apply_state) DONE — copied byte-identical to jail/AAUnlimited/mod/ + forced in jail forcedconfig.
- ✅ debug_tool.py Python-CLI built+tested; Lua engine-setter built (flag-driven).
- ✅ run_orchestrator.bat crash fixed.

---

# 5. HANDOVER_transfer_2026-06-24.md — Instant transfer (slave → jail) + SSOT Model A

## Headers / topics
- 0. TL;DR — wo wir JETZT stehen
- 1. DAS MODELL A (Transfer mechanics)
- 2. VERIFIZIERTE FAKTEN (live)
- 3. GEÄNDERTE / NEUE DATEIEN
- 4. ★ KEYSTONE BEWIESEN: AddCard funktioniert
- 5. ★ NÄCHSTER SCHRITT: 2b — Selbst-Werte injizieren
- 6. DANACH: 2b + 2c
- 7. OFFEN: Auto-Save im ~7-Tage-Fenster
- 8. UMGEBUNG / FAKTEN
- 9. UPDATE — Modul-Scan + 2c gebaut
- 10. 2c VOLL — Beziehungs-Reconciliation (char↔char + PC)
- 11. BEZIEHUNGS-GEDÄCHTNIS — kontinuierlicher Snapshot (Sims-Modell)
- 12. WIE MORGEN STARTEN
- 13. GIT / REPO

## Facts
- **Design pivot (user):** transfer happens INSTANTLY on enslaving, NOT at end-day. End-day = only WHEN the PC physically enters jail and finds the already-transferred inmates.
- **SSOT Model A:** commit-on-save, derive-on-load, day-dated. Single-save-slot per playthrough (saving always overwrites — no multiple timestamps). **The DB is the only history store** (the game has none).
- **Transfer flow:**
  1. Combo completed (`master_slave.lua`, school) → provisional: live-preview `KickCard` (deferred to `on.end_h`/`on.period` since KickCard mid FORCE_H scene can crash). Char remembered in `enslaved_uncommitted`. No commit.
  2. `on.save_class` (you save) → COMMIT: append `<nDays>\t<name>\t<gender>\t<self>` to `school/_orch_slave_commits.flag`. Not saved → no commit → jail stays empty.
  3. Orchestrator `transfer_sync` thread (every 1.5 s): ingests commits idempotently into `transfers` journal (`_playthroughs/<key>/memory.db`), reads school's current day from `school/_orch_day.flag` (written by `logperiod`), derives inmates for that day (`residents_as_of`), writes `jail/_orch_jail_inmates.flag` as `<name>\t<cardfile>\t<gender>`.
  4. `jail_intake.lua` (jail) reconstructs roster on `on.load_class`/`on.period`/`on.room_change`: KickCard each non-inmate (except PC) + AddCard each inmate not yet present.
- **`KickCard(seat)`** = correct signature, runs clean. Registered in `AAUnlimitedDll.dll` (ASCII+UTF-16 confirmed) with `AddCard`, `SafeAddCardPoints`.
- **Live self-value schema:** readable is `inst.m_char.m_charData.m_character.{virtue,intelligence,strength,sociability}` (values 1–3 = RANKS). Path `m_charData.virtue` (without `.m_character`) returns NOTHING. Airi: `virtue=0;intelligence=2;strength=1;sociability=3`.
- **PC detection:** `GetCharInstData(seat).m_char == GetPlayerCharacter()` (idiom from `music.lua`).
- **`AddCard(fileName, femaleBool, seat)` — LIVE PROVEN.** Format = **bare `"<Name>.png"`** (NO folder prefix; gender-bool picks `data/save/Female|Male`). Gender: `0`→`false` (male), else `true`. **Only call at STABLE moment (Period 9, home-screen — like `undyingAddCards`); mid-load fails.** Read period in jail via `logperiod`'s `_orch_period.flag` (direct `GetGameTimeData()` gave `-1` in jail_intake). Proof: `addmissing@p9: ADDED={Takagi Saya@0(Takagi_Saya.png)}`.
- **Loose cards exist for EVERY roster char** in `school|jail/data/save/Female|Male/<Name>.png` (e.g. `Shimizu_Airi.png`). The 25 "missing" names from the `.json` are historical blocks, not in roster → every enslavable char has a card. No `.sav` export needed.
- **jail-twin must be full copy** for filter-retain; `.sav` school=1.9 MB vs old pruned twin=230 KB. The `.json` is only AAU data store (roster is in the `.sav`).
- **Self-value injection PROVEN (2b):** `m_charData.m_character.<field> = value` works. Proof: `INJECTED={Shimizu Airi{virtue=0;intelligence=2;strength=1;sociability=3}, Takagi Saya{virtue=2;…}}`.
- **Setter family in DLL confirmed:** `SetCardVirtue/SetCardIntelligenceValue/SetCardStrengthValue/SetCardSociability(seat, value)` (verify signatures live like KickCard/AddCard).
- **Journal logic unit-tested (no game):** idempotent ingest ✓, day-dated derivation ✓, return (`to_world='school'`, last-write-wins) ✓. Day3=empty, Day5=[Kanata], Day7=[Airi,Kanata], after return Day8=[Airi].
- **Module-scan DONE (read-only):** `module_scan.py` reads all 466 module files from `school/data/override/module/` (Format: `DWORD name_len + name(UTF-16) + DWORD desc_len + desc(UTF-16)` + trigger tree) → `module_catalog.json` + `.md`. Example hits: "Corruption" (forceful → loses virtue → corrupted style), "Sex Addict" (loses virtue without sex), Chaste Cherisher, Abstinent, Banchou, Jailer, Blackmailer.
- **aaUd card format (Version 3):** member stream = `Vers`+Version, then 4-byte-LE tags; module member = `TrMd` = `int32 count` + elements; each element = `int32 name_len` + UTF-16LE name + params. Live-read from real cards (Airi 9 modules "Sugar Lips…", Sasaki 13 "Blackmailer…"). Chunk edit = standard (length + CRC32 new).
- **Action IDs (from `triggers_supplemental.lua` getActionName, 0–96+):** ENCOURAGE=0, PRAISE=2, INSULT=33, FIGHT=34, FORCE_IGNORE=35, FORCE_SHOW_THAT=36, FORCE_PUT_THIS_ON=37, **FORCE_H=38**, HEADPAT=44, KISS=46, TOUCH=47, MURDER=82, SLAP=83.
- **Beziehungs-API (`triggers_supplemental.lua`):** `GetLoveTowards`/`GetHateTowards`/`SetPointsTowards`, `createRelationshipPointsDump`/`restoreRelationshipPointsFromDump`, `createHStatsDump`/`restoreHStatsFromDump`.

## [LATENT] unused / for-later findings
- **[LATENT] Auto-Save in ~7-day window** — what if player doesn't save? Currently no commit = jail empty. Wanted: auto-save fn at day-change → orchestrator triggers save of active world + capture of inactive → commit to journal. Plus simultaneous saves (Model A = SSOT as sync point, no physical double-save). Not built.
- **[LATENT] char↔char relationship reactivation** — pairs whose both ends absent SLEEP in SSOT, reactivate when counterpart joins (Boyfriend-join case). Dedup via present-set signature. Built into restore_rels but counterpart-join path needs frische enslaves to test.
- **[LATENT] `ingest_rel_commits`** (old enslave-time relationship variant) — remains UNUSED in code after the rel_snapshot redesign (§11). Kept but dead.
- **[LATENT] Return path jail→school** — `to_world='school'` last-write-wins logic exists in journal, but "load old save" is NOT a game feature (single-save-slot); day-dating serves as history/auto-save substrate. Return path build still open.
- **[LATENT] social_wealth** carried in `self` string (threshold bonds>=3, tunable) for later module-map; NOT written to char (inject_self ignores it). Derived per inmate from `char_rels` (`pdb.social_wealth`).
- **[LATENT] HStatsDump / createHStatsDump / restoreHStatsFromDump** — relationship/H dump-restore building blocks mentioned, H-stats restore not yet wired into transfer.
- **[LATENT] jail-world mechanics (future):** map-node blocking (reactive eject + storage-flag, progressive) + jail=night-only (`on.period`-hold) + optics (reskin PNGs).
- **[LATENT] RPG layer:** activity-DB, status-modules, loneliness/loner from social_wealth.

## [REJECTED] approaches / parked
- **[REJECTED: destructive + seat-naive]** Coupler-transfer `_transfer_to_jail` in orchestrator.py is PARKED (commented out) — was the wrong "all 1:1 roster copy". Real transfer is interaction-triggered (slave).
- **[REJECTED: redundant]** Enslave-time relationship capture in `master_slave` REMOVED after §11 redesign (continuous rel_snapshot replaces it). Only self-values remain there.
- **[REJECTED: seat-indexed pitfall]** Relationship/H values are seat-indexed → NEVER restore the dump 1:1 (points to empty/wrong seats in jail). Must resolve seat→char_id via live roster, store by identity. (2c rule, Notes 2.4c/2.4d + §12.)
- **Desync (jail-day ≠ school-day) is NOT a bug:** `transfer_sync` uses `read_day(school)` as anchor. By design.

## Open questions / limitations
- **2c jail-restore test pending:** fresh enslaves (two chars with relationship, both → jail) → debug line `RELS={A->B(...)}` in `jail/_orch_jail_debug.flag`.
- **LIMITATION:** relationships only captured for chars still in school at capture time. Already-transferred inmates (pre-2c-code) have NO rels → not retrofittable. Old Airi/Luka relationships lost (never snapshotted).
- **jail-twin behavior (safe):** "keep present inmates (by name), add missing via AddCard." Later switch to "always reload from SSOT/adapted card" (re-AddCard even present inmate to load adapted card) — for module-evolution.

## Files
- `school|jail/master_slave.lua`, `logperiod.lua` (+`_orch_day.flag`), `jail_intake.lua` (NEW, jail-only), `playthrough_db.py` (transfers journal + char_rels), `orchestrator.py` (read_day, _card_index/resolve_card_file, write_jail_inmates, transfer_sync thread), `rel_snapshot.lua` (school-only).
- Flags: `school/_orch_slave_commits.flag`, `_orch_day.flag`, `jail/_orch_jail_inmates.flag` (`name\tcard\tgender`), `_orch_jail_debug.flag`, `_orch_ms_debug.flag`, `_orch_rel_commits.flag`, `_orch_rel_snapshot.flag`, `_orch_jail_rels.flag`. Removed (stale): `_orch_slave.flag`, `_orch_slave_snapshot.flag`.
- DB tables: `transfers`, `char_rels(from_id,to_id,love,liking,disliking,hate)`, `relationships`.

## Git / repo facts (§13)
- Versioned on GitHub: `https://github.com/i0am0lost/MWA2-0.001` (public, tag `v0.001`). Remote `clean` → `MWA2-0.001`, upstream `main` → `clean/main`. Push autonomous (creds in Windows Credential Manager). Token can push but NOT delete (`delete_repo` missing).
- **Old repo `i0am0lost/MWA2`** (first push leaked personal paths/email) → set private. Do NOT use; canonical = `MWA2-0.001`.
- Repo holds ONLY project tooling; `.gitignore` excludes ~21 GB game folders `school/`+`jail/` and saves. Fresh clone needs an AA2/AAUnlimited install placed as `school/` + `jail/`.
- **Paths now PORTABLE:** `orchestrator.py` & `_re/*.py` use `_BASE = os.path.dirname(__file__)` instead of hardcoded `D:\...`. README is ENGLISH (community landing page), explains project as generic multi-world extension (jail = first instance, multiplicable). Detail docs stay German.
- **LESSON:** genericize personal paths (username, email, absolute paths) BEFORE any push.

---

# 6. HANDOVER_master-slave_2026-06-24.md — Config repair + master/slave trigger

## Headers / topics
- 0. TL;DR
- 1. ★ CONFIG-REPARATUR (NIE wieder Mods ausschalten)
- 2. ★★ master/slave-TRIGGER
  - 2.1 AAU Lua-Event-System
  - 2.2 Der Mod master_slave.lua
  - 2.3 NICHT als AAU-Card-Modul, sondern Lua-Mod
- 3. NÄCHSTER BLOCK: der Transfer
- 4. DATEI-/ZUSTANDS-STAND
- 5. UMGEBUNGS-FAKTEN

## Facts
- **`table.dump` bug FIXED** (`init.lua` Z.~120, school+jail): `string.format("%q", v)` crashed on `userdata` values → broke config serialization mid-way → `savedconfig` truncated to ~3 lines (mods table + `res_play` gone). Fix: a `userdata`/`thread` branch before the `%q` branch emitting `nil`. → savedconfig now survives every exit.
- **savedconfig restored** from user backup → school+jail have `res_play="1920x1080"` + all 30 mods (incl. **`win10fix`** = low-FPS fix). **Resolution = 1920×1080 (16:9).**
- **Backup path (READ ONLY): `<AA2-clean-install>`** — clean reference install. `AA2MiniPPX\AAUnlimited\savedconfig.lua` = the target config.
- **g_var conflict resolved:** `extsave` + `orch_savename` both patched `0x470B0`. Now `extsave.lua` exports its g_var (`rawset(_ENV, "_orch_g_var", g_var)`), and `orch_savename` uses the shared value instead of a second patch (fallback: own patch if extsave inactive). Both in school+jail.
- **savedconfig mirroring school→jail:** `mirror_config_school_to_jail()` in orchestrator.py copies school's savedconfig over jail's at start (guard: only if >50 B). → jail launches with school's list.
- **PC actions come via `on.answer(resp, as)`** — NOT `on.move` (that's NPC-AI only). Template: `mod/geass.lua` (Absolute Obedience). answerstruct `as`:
  - `as.askingChar.m_thisChar == GetPlayerCharacter()` → actor is PC.
  - `as.answerChar` → target of the action (`seat_of()` via `.m_seat` / `.m_thisChar.m_seat`).
  - `as.conversationId` → the action ID.
  - `as.answerChar.m_lastConversationAnswerPercent` → success-% (geass sets it to 999).
- **PC = Cox Robert = Seat 24** (green "Pc" badge; `GetPlayer()`/`GetPlayerCharacter()`). `on.move` actors are always NPCs (seat 24 never appears there).
- **Action IDs:** ENCOURAGE=0, PRAISE=2, INSULT=33, FIGHT=34, FORCE_IGNORE=35, FORCE_SHOW_THAT=36, FORCE_PUT_THIS_ON=37, **FORCE_H=38**, KISS=46, TOUCH=47, HEADPAT=44, SLAP=83, MURDER=82.
- **Only actions with "answer" fire `on.answer`** (INSULT, FORCE_*, KISS, PRAISE ✓; some mt-actions only via `on.move`). FIGHT (34) DID come through `on.answer` in test.
- **Other events:** `on.card_expelled(actor0, actor1, murder)`, `on.start_h`/`on.end_h`, `on.convo`, `on.period`, `on.save_class`/`on.load_class`.
- **master_slave.lua:** Combo `{INSULT=33, FIGHT=34, FORCE_H=38}`. `on.answer`: only if `isPC`; tracks combo progress per target-seat (`progress[seat]`). Wrong action vs same target breaks its chain; actions vs others don't interfere. On completion → `dbg("*** ENSLAVED ...")` + append to `_orch_slave.flag` as `"<seat>\t<Name>\n"`.
- **LIVE CONFIRMED:** `*** ENSLAVED: seat 4 (Shimizu Airi) via INSULT -> FIGHT -> FORCE_H ***`; `_orch_slave.flag` = `4 \t Shimizu Airi`.

## [LATENT] unused / for-later findings
- **[LATENT] `as.answerChar.m_lastConversationAnswerPercent`** — success-% readable; geass sets it to 999 (force success). Not yet used in master_slave but available for gating.
- **[LATENT] Combo constant is easily editable** (`COMBO` at top of mod) — for tuning the enslave trigger.
- **[LATENT] `_orch_period.flag` from logperiod** + the `0x470B0` g_var patch mechanism — reusable for any save-name/period read.

## [REJECTED] approaches
- **[REJECTED: cannot author binary trigger logic as code]** master/slave built as Lua-mod, NOT AAU-card-module. AAU card modules (trigger-editor GUI, logic binary in card/.ppx) cannot be written as code. Limitation: no NEW interaction verbs (engine fixed) — only reaction to combinations of existing ones. (NOTE: later superseded by the module-format RE which DID make code-authored modules possible — doc 3.)
- **[REJECTED: never auto-disable mods]** User was angry about auto-disabling mods. Principle: never automatically deactivate mods. User maintains ONE mod-list (school); jail gets it automatically.

## Open questions
- jail-click-verification at 1920×1080 still open — fractions are 16:9, should fit; check on next couple (console shows px coords + window size).

## Transfer plan (§3, at the time)
- Chars migrate INDIVIDUALLY via the interaction (slave), at day boundary (later changed to instant). Transfer = Card (if new in jail) + Play-Data (char-internal values: virtue, corruption, traits, modules, stats → 1:1, friction emerges free). Relationships NOT 1:1 → "condense" to char-internal values (`social_wealth=high` → loneliness module).
- Play-Data = the proven JSON transfer (`inject_chars_to_json`, by name → hits current roster seat-block).

---

# 7. HANDOVER_jail-coupling_2026-06-24.md — Jail-save coupling / orchestrator

## Headers / topics
- ZIEL-FLOW
- ARCHITEKTUR
- WAS GEBAUT IST (Phase 1 Coupler-Monitor, Phase 2 Save-Erkennung, Phase 3 Lifecycle)
- BEDIENUNG
- RPG-SCHICHT — Fundament gebaut + BEWIESEN
- NÄCHSTE SCHRITTE (RPG)
- UMGEBUNGS-FAKTEN

## Facts
- **Jail-save = coupled twin** of a school-save (not its own playthrough). Coupling lives in Python layer + folder structure, NOT in the engine.
- **One save per folder** → jail's load-list is always unambiguous (top = only slot) → the "list re-sorts" trap is gone.
- **Structure:**
  ```
  <project-root>\_playthroughs\
    <save name without .sav>\
      jail\        <- exactly ONE jail.sav (+ .json) = the twin
    index.json     <- Registry: { "<key>": {status, origin} }
  ```
- **Junction:** `jail\data\save\class` is a junction the orchestrator re-points before each jail-load to `_playthroughs\<active>\jail\`. Re-point = `os.rmdir`(reparse-point) + `mklink /J` (atomic, no admin; removes only the link, never the target files).
- **Phase 1 — `jail_coupler()`** (background thread, 2 s tick): keeps jail coupled to currently-loaded school save. Couples only when safe; `couple_attempted` prevents infinite retry.
  - **Save-switch:** if jail loaded in ANOTHER class → `restart_world(jail)` (kill+relaunch to fresh title) BEFORE coupling, because live-reload over a running class crashes (`0x10E9C8`). Watchdog ignores intended kill (`restarting` flag). Mutex-restart live confirmed.
  - **`_switch_lock` (RLock)** serializes coupler-load and user `do_switch` (non-blocking → no UI freeze). JAIL-button appears only when jail ready for active save (`loaded_key==key`).
- **Phase 2 — `orch_savename.lua`** writes loaded save name to `school\_orch_save.flag` (mechanism = like extsave: patch @ `0x470B0` → `g_var` → name at +100, unicode). Forced in `forcedconfig.lua`. extsave inactive in school → no 0x470B0 conflict. `read_save_name()` reads key (name without `.sav`). `switch_jail_save(jail, key)` bends junction.
- **Phase 3 — Lifecycle:** `scan_playthroughs()` (at start): saves WITHOUT twin → `status=needs_port` (manual); with twin → `ready`; orphan index entries (school-save gone) → twin + entry deleted. `playthrough_watcher()` (5 s thread): new save → twin auto-copied (`create_twin`, `origin=auto`); deleted save → `delete_twin` + entry removed; manual twin of needs_port → raised to `ready`. `baseline` = saves present at start → never auto-copied.
- **RPG layer foundation proven (the JSON bridge):** Each save has a `.json` = AAU's per-char store (virtue, corruption, traits, modules, stats), keys `"<seat> <name>"`. AAU reads it back on load (`init.lua` `get/set_class_key` → `GetClassJSONData`). Editing it before load → values land in-game.
- **`playthrough_db.py`** (built, tested): SQLite per playthrough (`_playthroughs/<key>/memory.db`), tables `chars` (self_data JSON-blob, char_id = normalized NAME), `relationships`, `world_state`. `snapshot_chars_from_json` (60 seat-entries → 34 names) + `inject_chars_to_json` (atomic). CLI: `python playthrough_db.py <db> snapshot|inject|dump`.
- **END-TO-END PROVEN (marker test):** school `.json` marker `intelligenceValue=9999` → DB → inject jail `.json` → jail loaded → in-game `get_class_key` read `9999` at all 11 checked chars. JSON bridge carries.
- **KEY INSIGHT:** mapping must run by **name → CURRENT seat**, NOT historical json-seat. The `.json` accumulates old `"<seat> name"` blocks; only chars whose current roster-seat = their json-seat got hit in test 1. inject/verify must map live roster (`GetCharInstData`) against names.
- Backups: `_backup\jail_class_premigration` (original jail NEW HOPE save), `_backup\empty_class_orig`.

## [LATENT] unused / for-later findings
- **[LATENT] `_transfer_to_jail()` PARKED** — exists + works but the call in `_couple_jail` is commented out ("all 1:1" is destructive + seat-naive). Reactivate once real logic stands. (Carries to doc 5 where the slave-driven transfer replaces it.)
- **[LATENT] needs_port automation** — once transfer logic stands, automate manual old-save porting via `on.load_class` trigger.
- **[LATENT] jail-click transition cover** — briefly thawing the suspended DirectX window; user accepts as systemic/harmless.
- **[LATENT] World_state table** in memory.db — exists, usage not detailed.
- **[LATENT] `restart_world` crash address `0x10E9C8`** — live-reload-over-running-class crash site (RVA). Noted, used as the reason to kill+restart.

## [REJECTED] approaches
- **[REJECTED: destructive/seat-naive]** "All 1:1 roster copy" transfer (`_transfer_to_jail` direct) — overwrites jail with school + seat-naive. Parked.
- **[REJECTED: covers neither new class nor save-switch]** Earlier one-time preload at start — replaced by the coupler-monitor.
- **[REJECTED: pure copy of needs_port]** A plain copy of an existing save would dump the full school roster into jail → manual porting (roster-cleaned twin) required instead.

## Next steps (RPG)
- Roster-seat mapping at snapshot/inject (live roster name+seat, not blind json-blocks).
- Decide which self_data fields transfer 1:1 vs which to exclude.
- Relationships + condensation (char↔char NOT 1:1; social_wealth → loneliness module).

---

# 8. HANDOVER_load-RE_2026-06-24.md — Load function / auto-load RE

## Headers / topics
- 0. TL;DR
- 1. Warum "kein Funktionsaufruf" — Beweiskette
- 2. KERN-RVAs
- 3. Methodik die FUNKTIONIERT
- 4. UMGEBUNG / DATEI-ZUSTAND
- 5. AA2-LADE-ARCHITEKTUR
- 6. ★ NÄCHSTER SCHRITT: "B" robust machen
- 7. WIE DIE NÄCHSTE SESSION STARTEN SOLLTE

## Facts (RE of AA2Play.exe load path — all RVAs relative to file ImageBase 0x400000; ASLR ON → runtime VA = RVA + GameBase)
- **GameBase varies per launch** (seen: 0x6C0000, 0x4D0000, 0xA20000). Absolute operands in disasm = file-VA (preferred base). Logs/dumps = runtime-VA. Always think GB-relative.
- **KERN-RVAs:**
  | RVA | What | Note |
  |---|---|---|
  | `0xF36D0` | SAVE function | `proc_invoke(GB+0xF36D0, 0, data)`; used by `mod/extsave.lua`. `data = ptr_walk(g_var,0x18,0x28,0)`, g_var via patch @ `0x470B0`. |
  | `0xF3C00` | LOAD function | `load(ECX=wchar_t* saveName, [stack]=data)`, `ret 4`. CreateFileW READ@0xF3C9F, ReadFile@0xF3D17, activates 25 seats. |
  | `0xB2680` | Load wrapper | `this` in EAX; `esi=[edi+0x1c]`=container; `call 0x413FF0`(Reset); name from `[edi+4]+0xE2A0`; `data=[[edi+0x1c]+0x28]`; `call 0xF3C00`; `ret 0`. Only reached via tail-jmp. |
  | `0xB24D0` | Thunk H | `eax=[esp+4]`(context); `eax=[eax+0xE29C]`(=this/load-manager); `jne; jmp 0xB2680`. → `this=[context+0xE29C]`. |
  | `0xB2440` | enqueueLoad | `func(context)`; `new(0x30)`→load-manager; ctor `0x4b2390`; `mov [context+0xE29C],eax`. Per-tick via H. |
  | `0x4b2390` | Ctor load-manager | `[obj]=vtable 0x72842c`; `[obj+4]=context`; `[obj+0x1c]=[context+0xE21C]`(container, COPIED). |
  | `0x413FF0` | Container Reset | reads object from **ESI** (non-standard convention!) → `proc_invoke` can't call it directly. |
  | `0x1AEEE0` | Dispatch loop | calls callback-table per tick with arg = global `0x767f48` (file-VA; = context object, RVA 0x367F48). |
  | `0x1AF4FC` | enqueueLoad caller | menu-action dispatch (synchronous on load-click). |
- **Context global:** file-VA `0x767f48` → RVA `0x367F48`. Fields: `+0xE29C`=load-manager(this)-slot, `+0xE21C`=container-slot (RVA `0x376164`), `+0xE2A0`=save-name (std::wstring), `+0xD774`=class-data-manager substruct (vtable `0x731818`). Menu-state on menu object (esi): `+0x7F4` (screen), `+0x7EC`, `+0x8D8`.
- **In-world confirmed (one run, GB=0xA20000):** `this=0x1B9E9550`, `container=[this+0x1c]=0x196E37C0` == g_var-chain-container == `[context+0xE21C]`. container+0x28=data, data+0x394=container.
- **Save-load is a UI/menu-state-machine action** (polled mouse input → state machine → per-tick dispatch). `enqueueLoad` synchronous chain entirely in `0x1AD000–0x1AF000`: `enqueueLoad ← 0x1AF4FC ← 0x1AE2AC ← 0x1ADCE7 ← 0x1AEF52`.
- **`[Menü+0x7F4]`** = screen-state (values 3,4,…), processed per tick (`0x1ADCE7`: `mov eax,[esi+0x7F4]; cmp eax,3/4…`). Save-name from list-selection (`rep movsd` 9 dwords @ `0x1AF4CE`).
- **Polled input:** game polls mouse-button state (DirectInput-like); does NOT react to `WM_LBUTTONDOWN`. PostMessage injection fails; only real device input (`mouse_event`/`SetCursorPos`) drives the menu. Synthetic clicks work only with HELD button (~0.25s).
- **Methodology that works:** in-engine mod detour (immune to anti-debug). Mod patches `g_poke(GB+addr, "\xE9"+rel)` jumping into an `x_pages` stub (executable; `malloc`=HeapAlloc is NON-executable due to DEP) → stub captures registers/stack, reproduces original bytes, jumps back. F6 (`on.keyup` key==117) dumps via `log.warn` → `aaunlimited` log.
- **Original bytes per function:** `0xB2680`: `83 EC 24 / 56 / 57` (5). `0xB2440`: `56 / 8B 74 24 08` (5). Both clean 5-byte boundary.
- **`peinfo.py`** (Dev-tool, `_re\`): modes `overview` / `<rva> [n]` / `xref <iat-va>` / `callers <rva>`. **ONLY with Python 3.12** (`py`/3.14 = broken stub, no capstone/pefile).
- **`orchestrator.py` `load_seq` for jail:** `[(0.344,0.939),(0.422,0.289),(0.640,0.750)]` (window fractions) + `BlockInput`.
- **Button layout (runtime, 1280x720 window):** Main menu "LOAD GAME" ≈ fraction x≈0.30, y≈0.94. Load-dialog: save-list top entry ≈ (0.42, 0.29); **Confirm = RIGHT blue button** ≈ (0.64, 0.75) (3 buttons bottom: red=cancel/back, 2× blue; right blue loads).

## [LATENT] unused / for-later findings
- **[LATENT] The entire RVA map** (load function `0xF3C00`, wrapper `0xB2680`, enqueueLoad `0xB2440`, thunk `0xB24D0`, ctor `0x4b2390`, container-reset `0x413FF0`, dispatch `0x1AEEE0`, context global RVA `0x367F48` + all field offsets) — built for cold-load-via-call, then NOT used (rejected, see below). Preserved for #10 (module-list direct write) and #5 (programmatic action triggering), and "if anyone ever wants to build load internally."
- **[LATENT] `0x413FF0` reads object from ESI** (non-standard) → cannot be called by `proc_invoke`. Important constraint if cold-load is ever revisited.
- **[LATENT] In-engine detour technique** (`g_poke` JMP into x_pages stub, DEP-aware) — proven, reusable for any function-RE / register capture.
- **[LATENT] `extsave.lua` SAVE call** `proc_invoke(GB+0xF36D0, 0, data)` with `data = ptr_walk(g_var,0x18,0x28,0)`, save-name at struct +100 unicode — the working save mechanism, reused by orch_savename.

## [REJECTED] approaches (with reasons)
- **[REJECTED: no callable load entry exists]** DEFINITIVE (static+dynamic proven): there is NO callable `load(saveName)` entry. Load is a UI/menu-state-machine action. Nothing to "grab out." Engine rebuild would be required = excluded.
- **[REJECTED: container empty at title menu]** Cold-load at title menu impossible: container/`this`/`data` are 0 at title menu; the container is created BY the load process itself (no isolated allocator — static+dynamic checked).
- **[REJECTED: more work, crashier, less robust]** The "internal state-poke" path — would bypass the input path that keeps several state fields consistent. Made obsolete by robust path-B (same end result for user).
- **[REJECTED: PostMessage doesn't drive menu]** `WM_LBUTTONDOWN` messages ignored (polled input). Only real device input works.
- **[REJECTED: don't rely on CE data breakpoints]** CE 7.6 "Find out what writes" on data-slot stayed silent (anti-debug suspicion) though address was correct. → don't rely on CE data breakpoints; use the in-engine mod detour.
- **DECISION:** the only viable auto-load = automated menu-click sequence (path "B") in orchestrator (real mouse input via `mouse_event` + `BlockInput`). Not a hack — the correct mechanism for a polled-input engine.

## Open questions / cleanup needed
- **⚠ CONFIG-CORRUPTION BUG** (independent): launcher throws `init.lua:121: bad argument #2 to 'format' (value has no literal form)` in `update_res`→`Config.save`→`table.dump` and truncates the mods table in savedconfig.lua. (Later FIXED in doc 6 via userdata branch.) Root cause = a config value has "no literal form" (a float/userdata).
- Cleanup: school `savedconfig.lua` back to real user config (extsave on, loadtest out); remove `loadtest.lua`; close CE.
- Path-B robustness build (§6): deterministic save-selection (list re-sorts alphabetically — fixed index tricky; jail's single-save makes it unambiguous; school needs name-logic); wait for load-screen (not fixed time); slow click (hold ~0.2–0.25s); verify success (in-world via period flag); foreground requirement (jail window must be foreground at click moment).
- Files changed needing cleanup: `_re\debug_launch_school.py` (NEW), `school\...\mod\loadtest.lua` (debug-mod, detours @ 0xB2440 + 0xB2680, F6=dump — NOT for product), `school\...\savedconfig.lua` (rewritten: loadtest=on, extsave=off, logperiod=off — must revert). Cheat Engine 7.6 at `C:\Program Files\Cheat Engine\` (can close; no x64dbg installed).

---

# 9. HANDOFF_next_session_RE.md — earliest RE briefing (2026-06-23)

## Headers / topics
- 0. TL;DR
- 1. Ordner-Realität
- 2. WAS GEBAUT WURDE (Dateien)
- 3. WIE MAN DAS SYSTEM STARTET / TESTET
- 4. KERN-BEFUNDE (4.1 PPeX, 4.2 Mutex, 4.3 Auto-Launch, 4.4 Fenster/Suspend, 4.5 AAU-Lua-API, 4.6 Tagesphasen, 4.7 #10)
- 5. ARCHITEKTUR-ENTSCHEIDUNGEN
- 6. ★ AKTUELLE AUFGABE: RE der Save-LADE-Funktion
- 7. UMGEBUNG / FAKTEN
- 8. OFFENE SCHICHTEN NACH DEM RE
- 9. WIE DIE NEUE SESSION STARTEN SOLLTE

## Facts
- **Folder reality:** clean install 21 GB UNTOUCHED (safety net); `school` 21 GB copy (active base); `jail` 21 GB copy. school+jail identical copies. Later: shared base via junction (`mklink /J`) → 63 GB → 21 GB. `AA2Play.exe` (32-bit) per world; shows AAU-launcher (iup dialog) then game main menu.
- **PPeX (4.1):** `PPeXM64.exe` = .NET-Core-3.1 server, unpacks `.ppx` mods, serves via global named-pipe `\\.\pipe\PPEX` (hardcoded). Stock = single-client (`Pipe.cs`: 1 NamedPipeServerStream, default maxInstances=1, no re-accept). **PATCHED to multi-client:** accept-loop with `MaxAllowedServerInstances`, thread-per-client, EOF-disconnect, `OnDisconnect`/exit only on LAST client. `Cache.LoadLock` serializes `load` requests → thread-safe. **Proven: 1 server serves 2 games.** Start: `dotnet PPeXM64.dll "<data-path>"`. **Keep stdin open** (else ReadLine-loop crashes on EOF). Server exits when last client gone.
- **Single-instance lock (4.2):** AA2 has NO hard early mutex (two processes coexisted while both hung before PPeX). Lock = named mutex `\Sessions\1\BaseNamedObjects\__AA2Play_Class__` (same name as window class), created only on FULL game start. **Bypass (version-independent, no exe-patch):** close the running instance's mutex handle via `DuplicateHandle(..., DUPLICATE_CLOSE_SOURCE)` → name free → next instance creates it fresh. → `_mutexfind` tool, mode `close`.
- **Auto-launch (4.3):** `dlg.lua` patch: env-var `AA2_ORCH_AUTOLAUNCH=1` → iup-timer (300ms) auto-fires `iup.ExitLoop()` → game boots without click. Mods NOT bypassed (each world loads its savedconfig normally).
- **Window/suspend (4.4):** game window class = `__AA2Play_Class__`. Orchestrator finds HWND via EnumWindows. Inactive world: `ShowWindow(SW_HIDE)` + suspend process (`NtSuspendProcess`) → frozen, no sound/CPU. Resume = instant. **Borderless-windowed mandatory** (exclusive fullscreen breaks when hiding). `mod/borderless.lua` active.
- **AAU-Lua-API (4.5, verified via `ScriptLua.cpp` + mods):**
  - Char access: `GetCharacter(seat)`, `GetCharInstData(seat)` (vacant→nil), `GetPlayerCharacter()`, `SetPlayerCharacter(...)`.
  - Char data (r/w): `inst.m_char.m_seat`; `inst.m_char.m_charData.m_forename/.m_surname/.m_gender`; `…m_charData.virtue` (set/get), stats (intelligence/strength/sociability/club…), `fightingStyle`.
  - Relationship/H: `…m_charData:m_hCompatibility(towards[,val])`; `…m_characterStatus:m_totalH/m_climaxCount/m_cherry/…(towards[,val])`.
  - Dump/restore: `createRelationshipPointsDump(seat,towards)`/`restoreRelationshipPointsFromDump(...)`; `createHStatsDump`/`restoreHStatsFromDump`.
  - Roster: `AddCard`, `KickCard`, `SafeAddCardPoints`.
  - Persistence: `getCardStorage(card,key)`/`setCardStorage(card,key,val)`, `getClassStorage`/`setClassStorage`; `SetClassJSONData`/`GetClassJSONData` (`set_class_key`/`get_class_key`).
  - Events: `on.period(new,old)` (return SETS the period!), `on.load_class`, `on.save_class(data)`, `on.room_change(inst)`, `on.move`, `on.card_expelled(a0,a1,murder)`, `on.keyup/keydown`, `on.ui_event(evt)`, `on.plan(ok,e,who)`, `on.d3d9_preload`.
  - Time: `GetGameTimeData()` → `.currentPeriod`, `.day` (0–6), `.nDays`. All settable.
  - Raw memory: `malloc`, `g_poke`, `g_poke_dword`, `peek`/`peek_dword`, `ptr_walk`, `proc_invoke(GameBase+offset, this, ...)`, `parse_asm`.
  - Misc: `iup.timer` works IN-GAME (Poser-proven). `play_path()/aau_path()/host_path()`. `log.warn` visible at default `logPrio=2` (`log.info`/`info()` NOT). Mod skeleton: `mod/<name>.lua`, first line `--@INFO ...`, `_M:load/unload/config`; new mods auto-detected, must be enabled in Scripts tab.
- **Day-phases (4.6, `CurrentPeriod`):** 1=day, 2=nothing, 3=first lesson, 4=first break, 5=sports, 6=second break, 7=club, 8=end, 9=home again, 10=sleep. **Home-screen (Quit/Title/Save/Load/sleep) = Phase 9.** Sequence is variable (engine can skip phases, e.g. 4→7).
- **SAVE function:** `proc_invoke(GameBase+0xF36D0, 0, data)` (extsave.lua `quicksave`). `data = ptr_walk(g_var, 0x18, 0x28, 0)`; g_var set up via memory-patch at `0x470B0`. Save-NAME at struct offset +100 (unicode), see `save_name()`.
- AA2Play.exe imports `CreateWindowExW`, `RegisterClassExW`, `CreateMutexW`, `CreateFileW`/`ReadFile`. Saves at `<world>\data\save\class\*.sav`.
- **Environment:** Python 3.14.2 via `py`. pywin32 NOT installed → use ctypes. .NET SDK 8.0.418 + 10.0.201; runtimes incl. netcoreapp 3.1.9. `git`, `dotnet` present. No disassembler installed initially. UTF-16 grep: `LC_ALL=C grep -aP`.

## [LATENT] unused / for-later findings
- **[LATENT] #10 (module list) status:** module-IN-USE-list is NOT Lua-writable. Workaround: pre-install custom module once + gate via card-storage flag. (RE could find the module-list memory layout → real write via `g_poke` → would solve #10 cleanly.) [This whole arc was later solved via the native AddModule RVA + reroute hook, doc 1.]
- **[LATENT] #5 (programmatic action triggering)** — "active intervention" class, the project's hard wall. RE function-map helps here.
- **[LATENT] Daily background ticks:** worlds "remember" via Python-resolver on the DB — inactive engine SLEEPS, is NOT loaded/simulated (Notes 4.8a). Apply on entry via Lua inject into the (resumed) world. → Load function NOT needed for ticks; needed only for cold-start-in-world (UX) and useful for #10/#5.
- **[LATENT] `SetPlayerCharacter(...)`** — listed as available, no current use.
- **[LATENT] `on.plan(ok,e,who)` (frequent), `on.ui_event`, `on.d3d9_preload`** — events available, not yet exploited.
- **[LATENT] `SafeAddCardPoints`** — roster/points helper, available.
- **[LATENT] `createHStatsDump`/`restoreHStatsFromDump`** — H-stats dump/restore, available, not yet wired into transfer.

## [REJECTED] approaches
- **[REJECTED: UX inacceptable]** Variant "load manually once per session" — rejected; auto-load required.
- **[REJECTED: fragile]** RE-free path = fragile mouse-click automation on the rendered menu → undesired (at this stage; later this very path "B" became the accepted solution after cold-load proven impossible).
- **[REJECTED: triggers Store-stub]** `python` in some shells hits the Windows-Store stub → use `py` for orchestrator. (Note: later inverted — Python312 `python.exe` is the canonical tooling interpreter; `py`/3.14 broke pip modules.)

## Distribution / architecture decisions
- ONE installer, all runtimes bundled (PyInstaller for Python; PPeX self-contained). World folders via junction (shared base), distribute only delta. Mutex-closer ported to Python (ctypes).
- Data manipulation in AAU-Lua; Python = orchestrator (server/processes/windows/DB/bridge).

---

# 10. HANDOVER.md — "Start-here" overall status (2026-06-23)

## Headers / topics
- 1. WAS DAS PROJEKT IST
- 2. DEINE WÜNSCHE — STATUS (table) + NICHT machbar / harte Grenzen
- 3. WAS GEBAUT IST (Dateien)
- 4. WO WIR GENAU STEHEN (Boot-Auto-Load, Tuning offen)
- 5. KERN-TECHNIK
- 6. ROADMAP NACH DEM BOOT-AUTO-LOAD
- 7. UMGEBUNG / TOOLING
- 8. SO STARTEST DU MORGEN

## Facts
- **Project:** second "Jail" mode (generically: multiple worlds) for Artificial Academy 2 (AAUnlimited). Multiple pre-loaded worlds, instant switch, persistent char-dev via a DB. End product: ONE installer.
- Folders: `AA2MiniPPX` (21 GB original, untouched), `MWA2\school` + `MWA2\jail` (21 GB copies = the two worlds). Game = `AA2Play.exe` (32-bit). Mods/PPeX installed.
- **User wishes status table:** #1 PPeX+instant-switch ✅, #2 one-startpoint both worlds preloaded jail hidden ✅, #3 background world pauses ✅, #4 don't bypass launcher mods ✅, #5 idiot-proof exit ✅, #6 all English ✅, #7 JAIL button on home-screen only ✅, #8 world-orientation label ✅, #9 land directly in jail-world 🔶 built tuning-open, #10 save-coupling 🔶 half, #11 shared base ⬜ planned, #12 one installer ⬜ planned, #13 optics per world ⬜ planned, #14 daily background dev ⬜ planned.
- **Core tech recap:** PPeX multi-client (`Pipe.cs`, pipe `\\.\pipe\PPEX`), single-instance mutex `__AA2Play_Class__` bypass via `DuplicateHandle(...,DUPLICATE_CLOSE_SOURCE)`, auto-launch via env `AA2_ORCH_AUTOLAUNCH=1` + iup-timer patch in dlg.lua, suspend `SW_HIDE`+`NtSuspendProcess` (borderless mandatory), load-fn RVA `0xF3C00` / wrapper `0xB2680`.
- **Boot-auto-load click coords** (window-relative, from 1920×1089 screenshots): `LOAD GAME (0.344,0.939)`, `top Save (0.422,0.289)`, `Done (0.640,0.750)`. In `WORLDS[*].load_seq`. `menu_wait` = 6 s.
- Day-phases: 1..10; home-screen = 9, sleep = 10, end = 8.

## [REJECTED] / NOT FEASIBLE (hard limits — important)
- **[REJECTED: crashes]** Hot-swap save mid-operation (reload running jail-class to another save) → CRASHES (RE-proven, global manager dangling). Solution: kill+restart (seconds).
- **[REJECTED: not practical]** Cold-load via direct function call (load save without menu-click) → not practical (RE-proven: container empty at menu, load deep in event/menu-state-machine). Solution: trigger the game's own menu-load ONCE at boot via UI-automation.
- **[REJECTED: not 100%]** "Completely without menu/logo" → not 100%: rendered menu must be visible+foreground to click → you briefly see the auto-load once per world at boot. All subsequent switches clean in-world.
- **[REJECTED: hard engine limits]** Roster-cap 25 / no new map geometry / no new action verbs → hard engine limits (workarounds: DB-rotation, reskin, repurposing).

## Open questions (at the time, mostly resolved later)
- Boot-auto-load "doesn't quite work" — not yet localized. Likely causes: timing (menu >6s; raise `menu_wait`), coords (window may be 1920×1080 not 1089; Y slightly off), logperiod not active in jail (in-world wait via period-flag fails).
- JAIL-button bug (showed at menu) → fix "only fresh period-flag (mtime < 2 s) counts" — verify next run.

## Environment / tooling
- Game-orchestrator: `py` (Python 3.14, stdlib+ctypes only). RE-dev tooling: `python` (3.12, has capstone+pefile) for peinfo.py. GameBase rebased at runtime (ASLR; peinfo uses file-base 0x400000). .NET SDK 8+10, runtime netcore 3.1.9. Memory-system `…\<unrelated-project>\memory\` = finance project, NOT this game project — canonical = the MD files here.

---

# CROSS-DOC EVOLUTION NOTES (how facts changed over time)

- **Module-on-card writing:** REJECTED early (byte-splice corrupts AUSS, doc 4) → pivot to GLOBAL POOL runtime-apply (doc 4) → then module-format fully RE'd making code-authored modules possible (doc 3) → then native `AddModule` RVA + reroute hook (doc 1) made even installation unnecessary (in-memory reroute on load). Cards now NEVER touched (doc 1 architecture correction).
- **Cold-load via function call:** fully RE'd (doc 8 RVA map) then REJECTED (container empty at menu) → menu-click automation "B" accepted (doc 8/10).
- **Identity key:** name-based char_id (docs 7-5) → then stable INT global `mwa_id` on card + SSOT re-key (doc 1), but on-card stamping later rejected; mwa_id stays internal SSOT key linked from cardfile.
- **Python interpreter:** `py`/3.14 for orchestrator (early docs) but Python312 `python.exe` is canonical for tooling (pip modules broken on 3.14); `run_orchestrator.bat` pinned to Python312 after the Tcl-teardown crash (doc 4).
- **Transfer:** parked 1:1 coupler copy (doc 7) → instant slave-driven transfer + journal (doc 5) → continuous rel_snapshot Sims-model for relationships (doc 5 §11).

---

# CORPUS 3/4 — DESIGN / TAXONOMY (detailed extraction)

# Master Blueprint — Design Knowledge Extraction

Source docs (all in `D:\Games\MWA2`):
1. `MODULE_CATEGORIZATION.md` — hand-curated categorization of all 466 AAU modules into the state→module "brain".
2. `EVOLUTION_MAP.md` — the rule engine: DB state → module assignment (thresholds, ladders). German-language doc.
3. `MOD_CARTOGRAPHY.md` — map of the AAUnlimited Lua mods, reusable mechanics, RE positions.

Core thesis across all three: a single-source-of-truth **DB** (`char_activity`, `char_rels`, `char_race_xp`, `chars`) is evaluated at an **end-of-day / world-boundary resolve** (Python). Accumulated state is thresholded to set **card-storage flags** that gate **pre-installed custom modules**. Modules are **NEVER written from Lua at runtime** — the flag is an OUTPUT of the DB. Design principle repeated everywhere: **evolution outcomes are EARNED, not assigned** — a char is *driven into* a module when accrued state crosses a threshold.

---

# 1. MODULE_CATEGORIZATION.md (`D:\Games\MWA2\MODULE_CATEGORIZATION.md`)

## 1.A Facts — field scheme & taxonomy

466 modules categorized on 7 axes (file → "Field scheme"):
- **function** (primary effect domain, pick ONE): SEXUAL, PERSONALITY, RELATIONSHIP, STATUS_ROLE, STATS_TRAINING, PREGNANCY, BEHAVIOR_AI, APPEARANCE, COMBAT_VIOLENCE, META_SYSTEM.
- **evo_role** (role in evolution system): **TARGET** (assignable transformation OUTCOME — the most important tag), **GATE** (status set at a world transition via card-storage flag), **SOURCE** (influences how a char develops/reacts but is not itself assignable), **NONE** (cosmetic/system).
- **relevance**: HIGH / MEDIUM / LOW to the jail/evolution project.
- **uncertain**: yes/no.
- **developable**: `yes` (earnable/developed; may also be innate — DB state can produce it), `innate` (starting/base trait only), `gate` (conferred by role/milestone, not counters), `system` (meta/utility/cosmetic).
- **race**: `<target_race>:<valence>` — DESIGNATION / BIAS / PREJUDICE / HOSTILE / OBSESSION.

## 1.B Facts — counts (file → "Counts")

Per function: SEXUAL 75, PERSONALITY 113, RELATIONSHIP 69, STATUS_ROLE 30, STATS_TRAINING 12, PREGNANCY 7, BEHAVIOR_AI 26, APPEARANCE 24, COMBAT_VIOLENCE 101, META_SYSTEM 9. (Total 466.)

Per evo_role: **TARGET 104, GATE 13, SOURCE 316, NONE 33**.

Per developable: **yes 259** (the rule-candidate pool), innate 154, gate 6, system 47. Uncertain (flagged for joint review): **12**.

The 6 explicit `gate` (role/milestone, NOT counter-driven): **Jailer, Detective, Banchou, Club Leader, Marriage, Killer**.

Race subsystem: 24 races × 7 modules = **168 race-subsystem modules** (1 Race + 1 Bias + 1 Prejudice + 3 Hostile families + 1 Obsession); 24 innate (DESIGNATION) + 144 developable; **72 HOSTILE-family rows** (24 races × 3 tiers).

## 1.C Facts — the canonical TARGET outcomes (notable modules called out as evolution endpoints)

These are the modules flagged HIGH relevance + `developable: yes` (TARGET) — the building blocks the evolution system drives chars *into*. With their threshold/driver hints from the `note` column:

**Sexual corruption / addiction ladder (HIGH):**
- **Corruption** — virtue loss/gain transforms style (corrupted1–4); "core evo outcome"; driver = virtue loss.
- **Sex Addict** — loses virtue without sex; "canonical evo outcome"; driver = high cum/H counters.
- **Semen Demon** — seeks cum when aroused (addiction-like); high cum/H counters.
- **Sex Crazed** — rapes when aroused; high arousal + force-H.
- **Compensated Dating** — solicits sex at station (prostitution outcome); corruption + low status.
- **Chained Maiden** — enslaved to virginity-taker; virginity taken by dominator.
- **Dark Semen** — sex lowers partner morality (corruption agent); high corruption.
- **Corruptor / Profane / Seducer** — corrupt others (agents of corruption); high corruption + force-H / romance.
- **Holy Semen / Saint / Puritan / Thot Patrol** — the PURITY counter-axis (high virtue outcomes): raise partner morality, mitigate corruption, reprimand/beat low-virtue people.

**Predator outcomes (HIGH, force-H driven):** Ambusher, Brute, Forceful, Kidnapper, Praying Mantis (kill-after-H), Easy Victim (the victim outcome; repeated victimization).

**Violence / yandere (HIGH):** Boiling Point (repeated forced sex → snaps & murders), Maneater, Mass Murderer, Murderous, Serial Killer, Final Solution, Yandere Type A/B/C, White Knight (protects rape victims — jail-relevant).

**Status / jail-relevant (HIGH):** Delinquent (truancy + authority conflict), Truancy (skipped-school counter), Loyal (sustained exclusive bond), Cheating (low loyalty + multiple suitors).

**Pregnancy (HIGH):** Baby Trap (wants-kids + obsession), Wants Kids (high love + maternal).

**Mood (HIGH):** Depression (3-stage mood/stat debuff; social isolation/loss).

**Training → transformation (STATS_TRAINING / COMBAT):** Bookworm/Studious/Musclehead (high study/exercise counters), Martial Arts Prodigy (HIGH — "jail martial-training reward"; high combat training), Battle Tactics / Martial Artist (combat training), Succubus (HIGH — gains strength via sex).

## 1.D Facts — RACE SUBSYSTEM (file → "RACE SUBSYSTEM")

The racial-evolution axis. 24 races, each with 5 valences (one module family each):

| valence | module family | meaning | developable | driver |
|---|---|---|---|---|
| DESIGNATION | `Race-X` | this char IS race X | innate | on card from creation |
| BIAS | `Bias-X` | more positive toward X | yes | favorable experiences with X |
| PREJUDICE | `Prejudice-X` | less responsive/negative toward X | yes | dominated/wronged by X |
| HOSTILE | `Hunter-X` / `Natural Enemy-X` / `Slayer-X` | wants to harm/kill X | yes | trauma/abuse / combat conditioning vs X |
| OBSESSION | `Obsession-X` | fixated on / loves X | yes | repeated H/love with X |

**HOSTILE is a 3-tier escalation ladder** (recorded as `X:HOSTILE/<tier>`):
- tier 1 `Hunter-X` (`/hunter`) — emotional hatred
- tier 2 `Natural Enemy-X` (`/natenemy`) — combat-strong vs X
- tier 3 `Slayer-X` (`/slayer`) — lethal capability vs X

**Full racial-standing axis (both directions):**
- Negative: `neutral → PREJUDICE → HOSTILE/hunter → HOSTILE/natenemy → HOSTILE/slayer`
- Positive: `neutral → BIAS → OBSESSION`
- DESIGNATION sits OUTSIDE the axis (who you are, not a standing).

The 24 races: Abomination, Alien, Angel, Beastfolk, Construct, Deity, Demon, Dragon, Elf, Fairy, Ghost, Greenskin, Human, Inorganic, Machine, Magic, Meme, Mutant, Plant, Psychic, Spirit, Undead, Vampire, Zombie.

Naming quirk: prejudice module for Demon is `Prejudice-Demons` (plural) — only inconsistency; mapped to `Demon`.

## 1.E [LATENT] — building blocks identified but NOT yet used (per EVOLUTION_MAP status, these axes are unbuilt)

The categorization names the full TARGET pool, but per the evolution map only the sexual/corruption + social axes are built. The following whole categories are **catalogued building blocks with no rule engine yet**:

- **[LATENT] Entire RACE SUBSYSTEM as rules** — 144 developable race modules. DB layer (`char_race_xp`) is built+unit-tested, but the *Resolve rules* that assign Prejudice/Hostile/Bias/Obsession are Backlog B1 (not yet wired). The 3-tier HOSTILE escalation (Hunter→Natural Enemy→Slayer) is fully specified but unbuilt.
- **[LATENT] Status / Slave-progression** — see EVOLUTION_MAP §4.5: a Slave module (unbroken→broken→trained) does not exist yet and must be built like Prisoner. Backlog B2.
- **[LATENT] Loneliness axis** — `social_wealth`-driven: "was high social wealth, now isolated → strong manipulation/exploitable effect." Inputs exist; rule is sketched but unbuilt (EVOLUTION_MAP §4.3).
- **[LATENT] Training → transformation outcomes** — Martial Arts Prodigy ("jail martial-training reward"), Bookworm/Musclehead/Studious, Succubus (strength-via-sex). Counters partly exist (`char_activity`) but no status/training counters yet (that DB row is ⬜ unbuilt, EVOLUTION_MAP §2).
- **[LATENT] Pregnancy axis** — 7 PREGNANCY modules incl. Baby Trap, Wants Kids (both HIGH TARGET); no pregnancy DB/resolve built.
- **[LATENT] Purity counter-axis** — Holy Semen, Saint, Puritan, Thot Patrol as the *positive* mirror of Corruption; design exists, no rule built.
- **[LATENT] Conditioning sub-mechanic** — a family of "more susceptible to X" TARGETs driven by repeated stimulus: Headpat Slut (headpat conditioning), Sugar Lips (kiss), Magnetic Tits / Hug Pillow / Sugar Lips (grope/hug/kiss conditioning), Naughty (arousal). A coherent latent "grooming/conditioning" axis.
- **[LATENT] Trauma outcomes** — #MeToo (revokes consent after H trauma), Sex Hater (H trauma / very high virtue), Philophobic (romantic trauma), Insane (extreme corruption/trauma). Latent "trauma" branch.

## 1.F [REJECTED] — resolved design decisions with reasons (file → "Related but NOT in the `race` column" & "UNCERTAIN")

- **[REJECTED: Futanari is anatomy, not a race-standing]** — Futanari stays OUT of the race subsystem axis; empty `race` cell, `developable: innate`. Never folded into a `Futanari:DESIGNATION` valence. It is an H-role + pregnancy-compat designation, not a prejudice/hostility/bias/obsession dynamic.
- **[REJECTED: race-flavored behavior modules are NOT race-standing]** — Neck Biter, Succubus etc. describe vampire/zombie-flavored behavior but are categorized as SEXUAL outcomes, not `race` cells.
- **Uncertain (flagged for joint review, not yet resolved — treat as soft-rejected pending review):**
  - **Armed** — combat-status TARGET vs item/equipment GATE — unclear.
  - **Summoner** — demon-summon ritual needing a loved-one sacrifice; spans relationship/combat/meta, hard to map to one threshold; tagged GATE but debatable.
  - **Blackmailer / Hidden Camera** — scheme vs role; Hidden Camera's mechanical effect is vague/joke-like.
  - **Attractive / Ugly / Cool Sunglasses** — appearance vs stat-buff; TARGET vs base SOURCE unclear.
  - **Haunted / Skinwalker / Human Guise / Flaming Head / Undying** — META possession/disguise/gimmick mechanics; "review whether they should ever be auto-assigned" (Haunted explicitly questioned).

## 1.G Headers / topic list

`# Module Categorization (for the state→module MAP / "brain")` →
- (intro: core design principle — outcomes EARNED not assigned; INNATE vs DEVELOPED; race column)
- `## Field scheme` (function / evo_role / relevance / uncertain / developable / race)
- `## Categorization table` (the 466-row table)
- `## RACE SUBSYSTEM`
  - `### Valence vocabulary (module family → valence → developable)`
  - `### Escalation ladder (full racial-standing axis)`
  - `### Racial-evolution rule pattern`
  - `### The 24 races`
  - `### Related but NOT in the `race` column (race-adjacent designations)`
- `## UNCERTAIN — for joint review` (COMBAT_VIOLENCE / SEXUAL / BEHAVIOR_AI / APPEARANCE / STATS_TRAINING / META_SYSTEM)
- `## Counts` (Per function / Per evo_role / Uncertain / Per developable / Race subsystem)

---

# 2. EVOLUTION_MAP.md (`D:\Games\MWA2\EVOLUTION_MAP.md`)

Subtitle: *"das Gehirn: Zustand → Modul (Schwellen-Regeln)"* — the hand-curated rule set translating DB state into module assignments, evaluated at end-of-day resolve.

## 2.A Facts — the pipeline (one-way street, §1)

```
Activity/Experience (engine events: on.end_h, on.move, master_slave …)
  ↓ capture mods write flags → orchestrator ingests
DB / SSOT (truth): char_activity, char_rels, char_race_xp, chars
  ↓ end-of-day resolve evaluates THIS map (Python, at day boundary)
Derived state: disposition=sex_addict, race_att[Human]=prejudice …
  ↓ at world switch (reload moment): set card-storage flag
pre-installed custom module renders: "Sex Addict" / "Prejudice-Human" / "Prisoner"
```
**DB → module, never the reverse.** Flag is an OUTPUT of the DB. Pure value effects (virtue/stats) also written directly from Lua (`char.virtue = X`).

## 2.B Facts — the DBs that feed the map (§2)

| DB source | status | feeds axis |
|---|---|---|
| `char_activity` (cumulative H counters: climax, totalH, cumIn*, riskyCum…) | ✅ built (school) | Sexual/Corruption |
| `char_rels` + `social_wealth` (relationship graph, positive bonds) | ✅ built | Social/Loneliness |
| `char_race` + `char_race_xp(char_id, other_race, positive, negative)` | 🔶 **DB layer built** (set/get-race, `add_race_xp`, `accrue_domination`, `race_attitude` ladder, unit-tested) | Race axis |
| Status/counter flags (dominance/training) | ⬜ B2 (with status layer) | Slave progression, Prisoner |

## 2.C Facts — rule schema (§3, the map format)

```yaml
rule: <id>
  axis:     sexual | social | race | status | stats   # grouping only
  outcome:  <module or module-tier>                    # what gets assigned/toggled
  when:     <condition over DB values>                 # threshold(s); AND/OR
  escalate: [<higher threshold> -> <stronger module>]  # optional ladder
  unless:   already innate/present                     # never double / never vs designation
  apply:    end-of-day resolve -> card-storage flag at next world switch
```
Thresholds (`THRESH_*`) are free tuning constants (Python), later calibratable.

## 2.D Facts — the example rules per axis (§4)

**§4.1 Sexual / Corruption (inputs already in `char_activity`):**
```
rule: corruption_via_H
  outcome:  Corruption (corrupted style)
  when:     activity.climax + activity.cumSwallowed + activity.cumInVagina > THRESH_CORRUPT
            AND char.virtue is dropping
  escalate: > THRESH_CORRUPT_HI -> Sex Addict
  unless:   already innate (e.g. starts as Sex Addict / Hoe)
```
Worked user trajectory: Attractive + non-Addict → in jail "covered in cum" (cumSwallowed/cumInVagina accumulate) → threshold → personality evolution → Corruption → Sex Addict.

**§4.2 Race axis — escalation ladder (Backlog B1):**
```
rule: racial_prejudice
  outcome:  <DominatorRace>:PREJUDICE         # e.g. Human:PREJUDICE
  when:     char.race != DominatorRace
            AND race_xp[char][DominatorRace].negative > THRESH_PREJ
  escalate: > THRESH_HOST1 -> <Race>:HOSTILE/hunter    # Hunter-X (emotional hatred)
            > THRESH_HOST2 -> <Race>:HOSTILE/natenemy  # Natural Enemy-X (combat-strong)
            > THRESH_HOST3 -> <Race>:HOSTILE/slayer    # Slayer-X (lethal)
  unless:   char.race == DominatorRace        # no prejudice vs own race

rule: racial_bond
  outcome:  <PartnerRace>:BIAS -> :OBSESSION
  when:     race_xp[char][PartnerRace].positive > THRESH_BIAS
  escalate: > THRESH_OBSESS -> <PartnerRace>:OBSESSION
```
race_xp source: domination event (master_slave) → negative vs master's race; loving H → positive vs partner's race. `chars.race` read externally from card modules at day boundary.

**§4.3 Social / Loneliness (inputs in `social_wealth`):**
```
rule: loneliness
  outcome:  loneliness/exploitable module
  when:     was social_wealth=high AND present_bonds == 0 (isolated in jail) for >= N days
```
Note (Notizen 2.4c): high social wealth + now isolated → strong manipulation effect; Loner (low) → different rule.

**§4.4 Status — GATE (set at transition, not counter-driven):**
```
rule: prisoner_status
  outcome:  Prisoner -> Ex-Prisoner -> Rehabilitated   # ONE module, 3 flag values
  when:     world transition school->jail (Prisoner) / jail->school (Ex-Prisoner) / threshold (Rehab)
  note:     GATE — by role/milestone, NOT by accumulated counter
```

## 2.E [LATENT] — planned / unbuilt rules

- **[LATENT] §4.5 Slave-progression (Backlog B2)** — explicit PLACEHOLDER: "module does not exist yet, must be built (like Prisoner)." outcome: `Slave: unbroken → broken → trained`; when domination/training counter crosses tier thresholds. status: BACKLOG.
- **[LATENT] Race axis rules (B1)** — DB layer built+tested, but the resolve rules of §4.2 are not yet wired into the engine.
- **[LATENT] Loneliness rule (§4.3)** — sketched; depends on social DB (built) but rule unimplemented.
- **[LATENT] Status/counter DB row** — dominance/training counters are ⬜ unbuilt (B2, "with status layer"); blocks both Slave progression and any training-counter outcomes.
- **[LATENT] §6 next build steps** (the unbuilt roadmap):
  1. Race-DB (B1): `chars.race` + `char_race_xp` + capture (domination/H → race) — analogous to activity DB.
  2. Resolve-Engine: Python module evaluating these rules at end-of-day (read DBs → write state).
  3. Custom modules + card-storage gating: **Prisoner first** (template), then Slave-progression (B2).
  4. Threshold calibration: tune the `THRESH_*` (free design decision).

## 2.F [REJECTED] / constraints

- **[REJECTED implicitly: no runtime Lua module-writing]** — modules cannot be written from Lua at runtime (§4.6 ref); therefore modules MUST be pre-installed and flag-gated. This is why the architecture is DB→flag→pre-installed-module rather than direct assignment.
- **No prejudice vs own race** — hard `unless` guard (`char.race == DominatorRace`).
- **Never double-assign / never override a DESIGNATION** — `unless: already innate/present`.

## 2.G Headers / topic list

`# Evolution Map — das „Gehirn": Zustand → Modul (Schwellen-Regeln)` →
- `## 1. Einordnung — Einbahnstraße` (the one-way pipeline)
- `## 2. Die DBs, die die Map speist` (DB sources table)
- `## 3. Regel-Schema (das Map-Format)` (YAML rule schema)
- `## 4. Beispiel-Regeln (Vorlage, je Achse)`
  - `### 4.1 Sexual / Corruption`
  - `### 4.2 Rassen-Achse — Eskalations-Leiter (Backlog B1)`
  - `### 4.3 Sozial / Einsamkeit`
  - `### 4.4 Status — GATE`
  - `### 4.5 Slave-Progression — Custom-Modul nötig (Backlog B2)`
- `## 5. Resolve-Ablauf (am Tageswechsel)`
- `## 6. Nächste Bau-Schritte (aus dieser Map)`

---

# 3. MOD_CARTOGRAPHY.md (`D:\Games\MWA2\MOD_CARTOGRAPHY.md`)

Subtitle: *"wiederverwendbare Mechaniken & relevante Positionen"* — complete map of all AAUnlimited mods (`school|jail/AAUnlimited/mod/`) with marked relevant hooks/RVAs/globals/APIs, tied to open project items. Stand 2026-06-25. Legend: ⭐ key for open item · 🔧 useful API/idiom · 🎯 RE position (RVA/global) · ◽ cosmetic.

## 3.A Facts — project-owned mods (§A, the orchestrator's own)

| Mod | Hooks | Function |
|---|---|---|
| `master_slave.lua` | on.answer, on.end_h, on.period, on.save_class | ⭐ Dominance combo INSULT→FIGHT→FORCE_H → slave; commit-on-save |
| `rel_snapshot.lua` | on.load_class, on.period, on.answer | ⭐ Continuous relationship snapshot → SSOT `char_rels` |
| `logperiod.lua` | on.period, on.load_class, on.keyup | ⭐ Day/period flag (`_orch_day/period.flag`) + live char dump |
| `jail_intake.lua` (jail only) | timer + load/period/room | ⭐ Roster reconstruction (KickCard+AddCard+Inject) |
| `orch_savename.lua` | on.load_class | 🔧 Reports loaded save name (jail coupling) |
| `loadtest.lua` | on.keyup | 🎯 RE test mod (detour 0xB2440/0xB2680, F6=dump) |

## 3.B Facts — reusable mechanics, each mapped to an OPEN project item (§B)

- **B1 Action-gating / blocking nodes** → open item "block map nodes/actions (jail dungeon, progressive)". Mods: `nomurder.lua` (`on.move` nulls a starting action: `conversationId=-1; target1=0` — minimal gating template), `butthurt.lua` (`on.plan` blocks a planned action with **chance + cooldown**), `triggers_supplemental.lua` (`on.move`, `on.card_expelled` — tracks started actions + card removal). `on.move` is read+write (action rewritable). Whitelist source = `const.lua`.
- **B2 Time/period control** → open item "jail = night only; forced switch-back at day boundary". `timewarp.lua`: `on.period(new, old)` returns modified period; pokes `GetGameTimeData()` (`d.day=(d.day+7±1)%7`); period space = `1..10`; `return targetperiod` holds/forces a phase.
- **B3 Room/node detection + COMPLETE ROOM MAP** → node-blocking + per-world optics. `cram_school.lua` has the **full room list** (`getRoomName(idx)`, index 0–52) + `isRoomInterior(idx)` — "the node vocabulary for jail gating." Hooks `on.roomChange` / `on.room_change`. **Reskin via folder-rename**: cram_school swaps lighting sets via `os.rename` in `data\sets\!lighting_night\` — idiom for "optics per world / jail=night" with no binary patch.
- **B4 H/activity introspection** → "Activity DB (H/climax counters → thresholds → states)". `climaxbutton.lua`/`facecam.lua`/`music.lua`: `on.start_h(hInfo)`, `on.end_h()`, `on.change_h(...)`; `hInfo.m_currPosition`, participant `m_charData.m_gender`; **`m_climaxCount`** is the counter source. → on.end_h + counter = activity-DB hook.
- **B5 Obedience / force answer** → jail dominance / "obedience" RPG layer; combo reliability. `geass.lua`: `on.answer(resp, as)` — `resp=1` forces "yes"; `m_lastConversationAnswerPercent=999`; PC-check idiom `as.askingChar.m_thisChar == GetPlayerCharacter()`.
- **B6 Custom text overlay** → node-block feedback ("you can't go there"). `subtitles.lua`: `AddSubtitles(text, fname)` shows arbitrary text (+`InitSubtitlesParams`). `notifications.lua` is styling-only — subtitles is the push path.
- **B7 PC control** → run PC/NPC autonomously in jail. `toggleautopc.lua`: `setPcAuto/getPcAuto` via 🎯 `peek_walk(GameBase+0x376164, 0x38)+0x2e3`. Reveals game-state context global `0x376164`.
- **B8 Autosave net** → "auto-save in ~7-day window". `extsave.lua`: `bAutosave`+`sAutosave "1 4 6 8 9"`; `on.period` auto-`quicksave()`; save call 🎯 `proc_invoke(GameBase+0xF36D0, 0, data)`.

## 3.C Facts — RE positions (§C, RVAs & globals; GameBase ASLR-relative)

Save fn `0xF36D0`; Load fn `0xF3C00`; Load wrapper `0xB2680`; `enqueueLoad` `0xB2440`; container reset `0x413FF0`; **live-reload CRASH** `0x10E9C8` (dangling); dangling manager global `0xB6264` (teardown question); Save/Load context global `0x767f48` (`+0xE21C` container, `+0xE2A0` name, `+0xE29C` action-slot); game-state context global `0x376164`; Save-struct `+0x64`=name(utf16), `+0x394`=CharArray, `+0x398`=valid-ptr.

## 3.D Facts — action vocabulary (§D1 `const.lua`)

Action IDs 0–113. The dominance combo: **INSULT=33, FIGHT=34, FORCE_H=38**. Others: MURDER=82, TOGETHER_FOREVER=81, TALK_*=15–19, STUDY_TOGETHER=20, INTERRUPT_*=63–65, H_END=66, BREAK_H=113, KISS=46, HUG=45, HEADPAT=44, SLAP=83, FOLLOW_ME=49, GO_AWAY=50, COME_TO=51.

## 3.E Facts — engine limits (§E)

- **25 seats fixed** (`for i=0,24`) — roster cap confirmed.
- **53 rooms fixed** (`getRoomName` 0–52, School gates(0)…Machine Room(52)). No new geometry → jail "nodes" = a gated subset of these 53; interior/exterior classified.
- **Reskin = folder/set swap** (lighting, override/shadow-set) — no binary patch needed.

## 3.F [LATENT] — noted-but-unused mod capabilities (building blocks not yet wired)

These are capabilities the cartography flags as available/useful where the corresponding project item is still open:
- **[LATENT] Progressive node-blocking (B1+B3)** — `nomurder`/`butthurt`/`triggers_supplemental` gating templates + the full 53-room vocabulary (`getRoomName`/`isRoomInterior`) are mapped but the jail-dungeon progressive gating is an OPEN item, unbuilt.
- **[LATENT] jail=night-only + forced day-boundary switch (B2)** — `timewarp.lua` `on.period` redirect is the proven mechanism; the world-switch enforcement is an open item.
- **[LATENT] Per-world reskin via os.rename (B3)** — lighting-set swap idiom identified ("optics per world / jail=night"); not yet applied to jail.
- **[LATENT] Obedience / "Gehorsam" RPG layer (B5)** — `geass.lua` force-answer is a building block for a jail dominance/obedience layer that is only conceptual.
- **[LATENT] Node-block feedback overlay (B6)** — `AddSubtitles` flagged as a generic text-push **candidate "to be verified"** (currently coupled to `on.load_audio`) — capability noted, not yet repurposed.
- **[LATENT] Autonomous PC/NPC in jail (B7)** — `toggleautopc` mechanism mapped; the autonomous-jail-walking item is open.
- **[LATENT] 7-day-window autosave net (B8)** — `extsave` mechanism + save RVA mapped; the orchestrator's auto-save window is an open item.

## 3.G [REJECTED] / hazards & cosmetic-excluded (§E, §F)

- **[REJECTED: live-reload]** — `0x10E9C8` is a **live-reload CRASH** (`cmp [esi+0x3c],edx`, dangling), and `0xB6264` is a dangling manager global flagged with a "teardown question." Implies live in-place reload is unsafe; the architecture uses full save/load + roster reconstruction (`jail_intake`) instead.
- **No new geometry possible** — locked to 53 rooms / 25 seats; jail must be a *subset* of existing rooms, not new map.
- **[Cosmetic/irrelevant (§F), excluded from project]**: borderless, facecam, hirestex, reshade, wined3d, win10fix, cram_school (lighting part only), aaface, JMCP, fixlocale, playtrans/makertrans/subtitles (translation function), nobra, **homosex (disabled)**, unlocks, jizou, poser/* (studio), edit/* (card-editor GUI — but module-editor RE tracked separately).

## 3.H Headers / topic list

`# Mod-Kartographie — wiederverwendbare Mechaniken & relevante Positionen` →
- `## A. PROJEKT-EIGENE MODS (Orchestrator)`
- `## B. WIEDERVERWENDBARE MECHANIKEN (für offene Items) ⭐` — B1 action-gating, B2 time/period, B3 room detection+room map, B4 H-introspection, B5 obedience, B6 text overlay, B7 PC control, B8 autosave
- `## C. ENGINE-/RE-POSITIONEN (RVAs & Globals)`
- `## D. HILFS-/REFERENZ-MODS` — D1 const.lua action vocabulary, D2 libraries, D3 triggers_supplemental dump/restore backbone
- `## E. ANHANG — Engine-Grenzen-Bestätigung` (25 seats, 53 rooms, reskin)
- `## F. KOSMETISCH/IRRELEVANT`

---

# Cross-doc synthesis — the LATENT design map (what's specified but unbuilt)

| Axis | DB | Resolve rule | Custom module(s) | Status |
|---|---|---|---|---|
| Sexual/Corruption | ✅ char_activity | ✅ §4.1 | Corruption (corrupted1–4) → Sex Addict | **built** |
| Social/Loneliness | ✅ char_rels/social_wealth | 🔶 §4.3 sketched | loneliness/exploitable module | **[LATENT]** rule unbuilt |
| Race (Prejudice/Hostile/Bias/Obsession) | 🔶 char_race_xp (DB built+tested) | ⬜ §4.2 (B1) | 144 dev race modules; 3-tier HOSTILE ladder | **[LATENT]** rules unwired |
| Status — Prisoner | n/a (gate) | §4.4 | Prisoner→Ex-Prisoner→Rehabilitated | **[LATENT]** "build first as template" |
| Status — Slave | ⬜ counter DB (B2) | ⬜ §4.5 placeholder | Slave: unbroken→broken→trained (DOESN'T EXIST YET) | **[LATENT]** must be built |
| Training→transformation | ⬜ status/training counters | ⬜ | Martial Arts Prodigy, Bookworm, Succubus | **[LATENT]** counters unbuilt |
| Pregnancy | ⬜ | ⬜ | Baby Trap, Wants Kids | **[LATENT]** |
| Purity (anti-corruption) | (virtue exists) | ⬜ | Holy Semen, Saint, Puritan, Thot Patrol | **[LATENT]** |
| Conditioning/grooming | (counters) | ⬜ | Headpat Slut, Sugar Lips, Magnetic Tits, Hug Pillow | **[LATENT]** |
| Trauma | ⬜ | ⬜ | #MeToo, Sex Hater, Philophobic, Insane | **[LATENT]** |

---

# CORPUS 4/4 — MAIN PROJECT NOTES (detailed extraction)

# Blueprint-Quellenextraktion — AA2_Jail_Projekt_Notizen.md

> Preservation-Pass. Quelle: `D:\Games\MWA2\AA2_Jail_Projekt_Notizen.md` (1167 Zeilen, DE).
> Stand der Notiz: 2026-06-24..27 verteilt. Legende der Notiz: ✅ fertig+bewiesen · 🔶 gebaut/Test offen · ⬜ geplant.

---

## TEIL 1 — VOLLSTÄNDIGER HEADER-BAUM (jede ## / ### in Reihenfolge)

```
# AA2 / AAUnlimited — "Jail"-Projekt: Erkenntnis- & Referenzdokument
## ★ STATUS — wo stehen wir (Stand 2026-06-24, spät) ★
## ★ ZUKUNFTS-MUSTER: Dispatcher-Modul für On-the-fly-Logik (Kern der Evolutions-Schicht)
## 0. Kurzfassung des Konzepts
## 1. Harte Engine-Limits (unveränderlich, kein Mod umgeht sie)
   ### Warum 25 so tief sitzt
## 2. Architektur des Jail-Modus
   ### 2.1 Zwei-Instanzen-Modell (der Kern)
   ### 2.2 Switch-Mechanik (Fenster-Sichtbarkeit)
   ### 2.2b Ressourcen & Save-Koordination
   ### 2.3 Einstiegspunkt: Heim-Menü-Screen (der Durchbruch)
   ### 2.4 Transfer Schule → Jail
   ### 2.4b Zustandstransfer: Card vs. Play-Data (KRITISCH)
   ### 2.4c Emergenter Konflikt durch divergierende Zustände (großteils GRATIS)
   ### 2.4d Roster-Rotation + DB als Long-Term-Memory (Antwort auf 25-Limit)
## 3. Tagesphasen & End-Day-Hook (QUELLCODE-BELEGT)
   ### 3.1 `CurrentPeriod` Expression
   ### 3.2 Resolver-Ablauf (Plan)
   ### 3.3 Phasen-Maschine & Teleport-Steuerung (✅ GELÖST 2026-06-23)
   ### 3.4 ✅ BESTÄTIGTE AAU-LUA-API (Architektur-Pivot)
   ### 4.1 Vorlage existiert: Jailer-Modul
   ### 4.2 Mechanismus (reaktiv, nicht gatend)
   ### 4.3 Knoten sperren / progressiv freischalten ("Dungeon Master")
   ### 4.4 "Andere kommen nicht rein"
   ### 4.6 Dynamische Module / kontextabhängiger Status (Prisoner→Ex→Rehabilitated)
   ### 4.8 Heimkehrer-Szenario: Partner ist weitergezogen (3 Schichten)
   ### 4.8a Täglicher Hintergrund-Tick (KORREKTUR zu "eingefroren")
   ### 4.7 Persistente Progression: Training/Transformation (Aktivitäts-DB)
## 5. Hint-System für versteckte Aktions-Combos
   ### 5.1 Problem
   ### 5.2 Dokumentierte Combos (Dictionary-Startinhalt)
   ### 5.3 Architektur des Hint-Systems (machbar, rein passiv)
   ### 5.4 NICHT empfohlen / unsicher: Klick-zum-Ausführen
## 6. Asset-/Optik-Layer (für Jail-Look)
## 7. Offene Punkte / vor dem Bau zu klären
## 8. Python-Komponenten (Bau-Checkliste für später)
   ### 8b. VERTEILBARKEIT — "Alles in EINER Install-Datei"
## 9. AAU-Trigger-Komponenten (Bau-Checkliste)
## 9b. ZUKUNFT: Multi-Welten-Skalierung
   ### Was skaliert (gratis bei generischem Bau)
   ### Was NICHT skaliert
   ### RAM-adaptive Lade-Strategie
   ### Die echte Obergrenze
   ### Konsequenz für den Bau JETZT
## 10. Referenz-Links
## 11. Wichtige Wahrheiten (nicht vergessen beim Bau)
## 12. SSOT / SAVE-KONSISTENZ — Befunde & TODO (2026-06-24)
## ★ GEPLANTE EVOLUTIONS-ACHSEN (Backlog, 2026-06-25) ★
```

> ANOMALIE: §4.5 fehlt (springt 4.4→4.6). §4.8/4.8a stehen VOR §4.7 (Reihenfolge im Doc so).
> Das STATUS-★- und Dispatcher-★-Kapitel stehen VOR §0. §4.x-Unterkapitel hängen strukturell unter ## 3.

---

## TEIL 2 — FACTS (Hard Facts, geordnet nach Thema)

### Engine-Limits (§1, §11)
- **Roster-Cap = 25 Chars/Klasse, hart, nicht erweiterbar.** Die 25 ist die Adressierungsbasis des ganzen Systems: Trigger-Expressions (ThisCard, TriggerCard, AnswerTarget, `[index]::Actor`) geben Seat-Index 0–24 zurück; Beziehungs-Matrix, Save-Format, Card Storage hängen am Index. 26. Card = jedes Array umschreiben + Save-Format brechen. Zusätzlich Performance-/Pathfinding-Deckel. AAU bohrt nur Maker-Slot-Limits auf (Gesichter/Haare/Tans/Kleidung = Asset-Auswahl), NICHT die Roster-Datenstruktur.
- **Keine neue Map-Geometrie** (Knoten nicht hinzufügbar). **Keine neuen Aktions-Verben** (talk/club/exercise fix; nur Konsequenzen umschreibbar).
- **Kein Cold-Loader callable** → Menü-Klick-Automatik (Boot-UI-Automation). **Live-Reload crasht** → Kill+Restart. **Modul-IN-USE-Liste nicht aus Lua zur Laufzeit änderbar** (kein API; Wiki+Quellcode).
- Leitprinzip: AA2 ist asset-/daten-moddbar bis zum Anschlag, aber engine-starr. Passiv (lesen/anzeigen/Assets tauschen/Saves manipulieren) = problemlos; aktiv (neue Geometrie/Verben/Aktionen ausführen) = harte Wand.

### Switch / Zwei-Instanzen / PPeX / Mutex (§2.1, §2.2, §2.2b)
- **Sofort-Switch-Modell:** beide Instanzen bei Launch vorladen, nur eine sichtbar; Switch = Fenster-Toggle. Immer nur EINE Welt aktiv (die mit dem Player); andere pausiert/suspendiert. Switch nur im Heim-Screen (Übergabepunkt). Keine Live-IPC — Prozess-Isolation; Brücke = Python über Save-Dateien.
- **VORAUSSETZUNG Borderless-Windowed** (`mod/borderless.lua` vorhanden). Exklusiver DX9-Fullscreen → Device-Loss beim Verstecken; NICHT nutzen.
- Win32 via `pywin32`/`ctypes`: `ShowWindow(SW_HIDE/SW_SHOW)`, `SetForegroundWindow`. Fenster über PID/Titel.
- **PPeX-Server (`PPeXM64.exe`) = single-client, global hardcodierter Named-Pipe `\\.\pipe\PPEX`** (quellcode-belegt `aa2g/PPeX` → `PPeXM64/Pipe.cs`: `new NamedPipeServerStream(name, PipeDirection.InOut)` ohne maxInstances → default 1; nach `WaitForConnection()` Endlos-Lese-Schleife, kein erneutes Accept). Pipe-Name hardcodiert. .NET Core 3.1.9 lokal vorhanden.
- PPeX wird vom **Launcher** gestartet (`loadPPeX()` in `mod/launcher/dlg.lua`), NICHT von `aa2play.exe`. Immer über Launcher starten.
- **AA2-Eigen-Mutex:** benannter Mutex `\Sessions\1\BaseNamedObjects\__AA2Play_Class__` (= Fensterklassen-Name), erzeugt erst beim VOLLEN Spielstart (nicht im Launcher), via `CreateMutexW`/`ReleaseMutex`. 2. Instanz stirbt mit 0-Byte-Log nach „Launch".
- **Beide Blocker gelöst (2026-06-23):** (a) PPeX-Multi-Client-Patch gebaut (`PPeXM64/Pipe.cs`: Accept-Loop mit `MaxAllowedServerInstances`, Worker-Thread/Client, EOF-Disconnect, Exit erst beim LETZTEN Client, `Cache.LoadLock` serialisiert `load`-Requests). Build mit .NET SDK 10, Target netcoreapp3.1. Artefakt `_ppex_src/PPeXM64/bin/Release/netcoreapp3.1/PPeXM64.dll`. (b) Mutex via `DuplicateHandle(..., DUPLICATE_CLOSE_SOURCE)` schließen → Name frei → nächste Instanz erstellt ihn frisch. Versionsunabhängig, KEIN exe-Patch. Tool `_mutexfind/` (.NET 8, NtQuerySystemInformation-Handle-Enum + Close; Modi list/close).
- **BEWIESEN:** 2× AA2Play.exe gleichzeitig (~245 MB je), beide am EINEN gepatchten Server. Orchestrator-Rezept: (1) PPeX-Server 1× über geteilte Daten; (2) Welt 1 starten → in-game warten → deren Mutex schließen; (3) Welt 2 → Mutex schließen; (4) Sofort-Switch per `ShowWindow`.
- **Ressourcen:** `SW_HIDE` gibt RAM NICHT frei; beide Instanzen voller Footprint ab Launch (~1–1,5 GB/Instanz, Total ~1–3 GB; PP2-Cache-Summe >1,5 GB = instabil/Wiki). CPU pausierter Instanz ~null. Disk zwei Installs ≈ 6–8 GB einmalig.
- **Save-Koordination:** Transfer-Write SYNCHRON abschließen, DANN Reload fire-and-forget. **Atomic Write:** Temp-Datei → `os.replace` (atomar auf gleichem Volume). Zusätzlich `.lock`-Flag. **Reload = Kill+Restart** (frischer Prozess liest Save garantiert; Live-Reload unsicher/crasht).
- Distributions-Modell: NICHT Komplett-Install verteilen; Python als Installer+Orchestrator. User behält eigenen AAU-Install (=school/Basis); Python legt jail als Geschwister-Ordner an, teilt schwere Daten (ppx/mods) per **Junction `mklink /J`**, enthält nur Delta (jail-Config, Background-Layer, Save-Vorlage, Custom-Module, gepatchter PPeXM64 + Original-Backup). EIN gemeinsamer Server bedient beide Instanzen; `loadPPeX()` muss unterdrückt/idempotent werden.

### Tagesphasen / `CurrentPeriod` (§3.1, §3.3, §3.4)
- **`CurrentPeriod` Expression** (Quelle: `AAUnlimited/Functions/Shared/Triggers/Expressions.cpp`), Integer-Mapping:
  `10=sleep · 1=day · 2=nothing to talk · 3=first lesson · 4=first break · 5=sports · 6=second break · 7=club · 8=end · 9=home again`.
- **Live geloggte Sequenz (logperiod-Mod, 2026-06-23):** `1→2→3→4→7→8→9→10→1`. Heim-Screen = **Period 9** ("home again"); Sleep-Klick → 9→10 → neuer Tag 10→1. End-Day-Hook = Übergang auf 8 (end) bzw. 9→10 (sleep). Overlay-Jail-Button einblenden bei `CurrentPeriod == 9`.
- **Phasen 5 (sports) + 6 (2nd break) wurden übersprungen** (4→7 direkt), ohne dass der Logger etwas verändert → Vanilla-Engine ⇒ Phasen-Sequenz ist **datengetrieben/variabel**, nicht starr 1..10 (stützt eigene Welt-Rhythmen).
- `GetGameTimeData()` → `.currentPeriod`, `.day` (0–6 Wochentag, lief 5→6), `.nDays` (absoluter Tageszähler, 6→7) — alle Felder **setzbar**. Brauchbar als Kalender für täglichen Resolver.
- **Phasen SETZBAR (gelöst):** AAU-Lua-Event `on.period(new, old)` — **Rückgabewert setzt die Ziel-Periode** (1–10). Beleg: `mod/timewarp.lua` (genau dieser Mechanismus; 14 Zeilen: `new = 1 + (old-1+10+back) % 10`), bestätigt in `mod/extsave.lua` + `mod/music.lua`. Der Set-Weg liegt auf **Lua-Ebene**, nicht im Trigger-Editor (deshalb war keine setzende „Action" belegt).
- "Time Warp" = `mod/timewarp.lua` (kein Tempo-Regler, kein Debug-Skip).

### Bestätigte AAU-Lua-API (§3.4) — Architektur-Pivot
> Quelle: lokale Lektüre `jail/AAUnlimited/mod/*.lua`. PIVOT: Python parst NICHT mehr die `.sav`-Binärdatei feldweise; State-Transfer läuft Lua-intern. Python = Orchestrator (Fenster-Switch, Prozesse, DB, Datei-Brücke, Overlay).
- **Char-Daten:** `GetCharInstData(seat)` (vacant→nil), `GetCharacter(seat)`, `GetPlayerCharacter()`/`GetPC()`. Felder: `inst.m_char.m_seat`, `inst.m_char.m_charData.m_forename`/`.m_surname`, `inst.m_char.m_charData:m_hCompatibility(towards[, value])` (Getter+Setter).
- **Schreibbar aus Lua (Quellcode-belegt `m_charData->m_character.virtue`):** `virtue`, `intelligence`/`strength`/`sociability`/`clubValue`, `fightingStyle` u.v.m. Lesen `char.virtue`, schreiben `char.virtue = X`.
- **Selbst-Werte vs. Beziehungs-Matrix getrennt adressierbar** (Beleg `mod/triggers_supplemental.lua`): `createRelationshipPointsDump(seat, towards)` / `restoreRelationshipPointsFromDump(seat, towards, dump, doNuke)`; `createHStatsDump(seat, towards)` / `restoreHStatsFromDump(seat, towards, dump, doNuke)`. → seat-paar-weiser Dump/Restore = der Transfer-Mechanismus existiert bereits.
- **Card Storage / Class Storage:** `getCardStorage(card,key)` / `setCardStorage(card,key,value)` (per-Card, persistent, überlebt Sessions); `getClassStorage(key)` / `setClassStorage(key,value)`; `getCardStorageKey(card)` (Schlüssel = `<seat LastName FirstName>`).
- **Events/Hooks:** `on.save_class(data)` / `on.load_class()` (idealer Transfer-/DB-Sync-Zeitpunkt); `on.period(new,old)`; `on.room_change(inst)` / `on.move(inst)`; `on.card_expelled(actor0,actor1,murder_action)` (Roster-Rotation-Hook); `on.keyup/keydown`, `on.convo()`, `on.start_h(hi)`/`on.end_h()`, `on.ui_event(evt)`, `on.launch()`; `on.dispatch_trigger(name,args)` + `dispatch_{string,int,bool,float}_trigger(...)`.
- **Roh-Speicher (Notausgang):** `malloc`, `g_poke`, `g_poke_dword`, `peek_dword`, `ptr_walk`, `proc_invoke(GameBase+offset, ...)`, `parse_asm`. `mod/extsave.lua` patcht damit live den Save-Code.
- **Mod-Gerüst:** Datei `mod/<name>.lua`, 1. Zeile `--@INFO <Beschreibung>`, Ende `local _M={...}; return _M`; `_M:load()/:unload()/:config()`; `mod_load_config(self,opts)`/`mod_edit_config(...)`; Logging `info(...)`/`log.info(...)`; `is_key_pressed(code)`.
- **In-game room/move-API (Probe `jail_probe.lua`, 2026-06-26):** `on.roomChange(seat,room,action)` + `on.move(inst)` feuern (NICHT `on.room_change(inst)`); `inst:GetCurrentRoom()` + `inst:IsPC()` funktionieren. `GetCurrentRoom` nur LESBAR — **kein Lua-Raum-Setter**.

### Confinement / Jailer-Mechanik (§4.1–4.4, STATUS jail-Welt-Mechanik)
- **Jailer-Modul (Vorlage, belegt):** sperrt Char in einen Raum (Dach); Fluchtversuch → zurückgebracht + bestraft; Gefangener verliert Stärke/Bewegung, wird exploitable; Rückholen via „follow me"-Aktion; Dauer je Vergehen. „Player can play as Jailer too" → PC-Confinement existiert.
- Mechanismus ist **reaktiv, nicht gatend**: über Room-change-Event + reaktives Zurückzwingen, NICHT über Gender-Gate an der Tür. Trigger sind **global** → eingrenzen mit `If ThisCard == TriggerCard`.
- **AAU-Action `NpcMoveRoom`** (Actions.cpp) schreibt nur `m_forceAction.movementType=2; .roomTarget=<raum>` — kein Funktionsaufruf, KI läuft hin; nur NPC, nicht PC. **`m_forceAction` ist NICHT Lua-erreichbar** (Userdata, kein Member-Zugriff). → reiner Lua-Eject versperrt.
- **ENTSCHIEDEN: Trigger-Editor-Modul-Weg** (statt `g_poke` auf Offset — riskant, CharInstData-Adresse aus Lua nicht zugänglich). Jailer-Modul liegt lokal (`*/data/override/module/Jailer`, 34KB binär, nur im Trigger-Editor lesbar), zu komplex zum Abwandeln → **neues Minimal-Modul spezifiziert in `CONFINEMENT_MODULE_SPEC.md`**. Bausteine verifiziert: Event `Room Change`; Expr `GetNpcCurrentRoom(seat)`, `GetPC()`, `GetThisCard()`; Action `NpcMoveRoom` = „Make Npc Move to Room". Stufe 1 = fester Zell-Raum (MVP); Stufe 2 = Zell-Raum/aktiv-Flag aus Card Storage (SSOT-Brücke).
- **Knoten sperren / Dungeon Master (§4.3):** `Wenn Raum betreten == Knoten_X UND CardStorage "Knoten_X_gebaut"==false → rauswerfen (+Notification)`. Flag umlegen → Eject feuert nicht mehr. Card Storage persistent. PC/NPC unterscheidbar (DM frei, NPCs gesperrt).
- **„Andere raushalten" (§4.4):** gleiche Room-change-Logik auf Nicht-Modul-Cards. **ACHTUNG Loop-Falle:** eigenes Rauswerfen = selbst ein Room-change → Endlosschleife → **Guard-Flag nötig**.
- **jail_phase.lua (gebaut, Test offen):** jail-only forciert; lenkt per `on.period`-Rückgabe **club (7) → end (8)** um → niemand in Clubräume; Tag wrappt. Block-Liste `REDIRECT` = eine Zeile zum Tunen (z.B. `[5]=8` für sports). Konfliktfrei mit anderen on.period-Mods (nil-Rückgaben gewinnen nicht). Fester Ausgangs-Knoten = train station.

### Card vs. Play-Data / Transfer-Modell (§2.4, 2.4b)
- **Zwei Datenebenen:** Ebene 1 = Card (PNG): Aussehen, Persönlichkeit, angewendete Module, **Basis-/Start-Werte** (Vorlage). Ebene 2 = Play-Data (im Klassen-Save, an Seat gebunden): gelebter Zustand — aktuelle Virtue, Beziehungspunkte zu allen Seats, Stimmung, Lover-Status, Modul-Veränderungen. Liegt NICHT in der Card.
- „lower virtue" ändert Play-Data, nicht Basis-Card. Master-Card NIE als Schreibziel (sonst Reset auf Original). AA2QtEdit ersetzt Cards in Klassen-Saves „ohne Character-History zu verlieren" → einzeln adressierbare Felder.
- **Transfer-Regel:** Char-interne Werte (Virtue/Vorlieben/Stimmung/Stats/Modul-Effekte) → TRANSFERIEREN. Beziehungs-Werte zu anderen Seats → klassen-spezifisch, NICHT blind mitnehmen.
- KickCard (raus aus school) + AddCard (rein in jail, Format **bare `<Name>.png`**, nur Period 9) = bewiesen. 2b Selbst-Werte (virtue/int/str/soc) injiziert + read-back-verifiziert.

### DB / SSOT / Roster-Rotation (§2.4c, 2.4d, §12)
- **AA2-Engine IST eine Kompatibilitäts-Maschine:** Interaktionen aus Werte-Vergleich zweier Chars; passt nicht → Engine erzeugt Reibung selbst (niedrigere Erfolgs-%, Ablehnung, Module feuern auf Diskrepanz). → divergierte Werte korrekt transferieren = Konflikt EMERGENT/gratis.
- **Roster-Rotation = Antwort aufs 25-Limit:** 25 Slots = rotierendes Fenster auf einen großen DB-Pool. Char raus → Zustand als long-term memory in DB; Char rein → Historie aus DB mitgebracht+angewendet. „Mehr als 25" → nicht gleichzeitig geladen, aber persistent erinnert.
- **DB-Schlüsselung: PRO PLAYTHROUGH eine `memory.db`**, NICHT global, NICHT pro Welt-Save. Schlüssel intern `char_id` (Ordner beschränkt schon auf Playthrough). Char-Zustand welt-übergreifend INNERHALB des Playthroughs (school+jail teilen `memory.db`); zwischen Playthroughs komplett getrennt.
- Drei-Stufen-Identität: (1) Basis-Card (Eve.png, read-only Vorlage); (2) Playthrough (Save 01 vs 02, eigenes Universum); (3) Char-Instanz-Zustand innerhalb eines Playthroughs.
- **jail.sav = gekoppelter Zwilling des school.sav, KEIN eigener Playthrough.** Kopplung lebt im Python-Layer + Ordnerstruktur, nicht in der Engine. Ordnerlayout: `Playthrough NN/ ├─ school.sav ├─ jail.sav └─ memory.db`.
- **Beziehungen char_id↔char_id, seat-unabhängig.** Beim Einfügen nur Beziehungen schreiben, deren Gegenpart gerade im Roster sitzt; abwesende → schlafen in DB, reaktiviert wenn beide präsent. Inject-Timing: nach Seat-Belegung, VOR Player-Interaktion, am End-Day/Heim-Übergang.
- **SSOT Modell A:** commit-on-save, tag-datiertes Journal, derive-on-load; **pro Playthrough nur EIN Save-Slot** (Speichern überschreibt immer); **die DB ist der EINZIGE Verlaufs-Speicher** (das Spiel hat keinen). `on.save_class` committet `<nDays>\tName\tGender\tWerte` → `_orch_slave_commits.flag` → Orchestrator `transfer_sync` ingestet ins `transfers`-Journal → leitet jail-Insassen für aktuellen school-Tag ab → `jail_intake` filtert.
- **Beziehungs-Reconciliation:** Beziehungs-/H-Werte sind seat-indiziert → Airi-Dump NIE blind restaurieren. Pro Beziehung: Gegenpart anwesend → char_id auf Live-Seat auflösen (Roster-Scan) → echte Beziehung schreiben; abwesend → char-intern VERDICHTEN, Beziehung schläft. Mechanik: create/restore-Dumps + seat↔char_id über Live-Roster-Mapping. AddCard-Basis-Karte ist richtige Grundlage (keine dangling refs).

### Dispatcher-Muster (★-Kapitel vor §0)
- **Problem:** Module laden/entladen = Trigger erst am Lade-Moment scharf (`InitOnLoad`/`InitTransferedCharacter` → `RegisterTrigger`). Modul zu schon geladenem Char dazulegen aktiviert seine Trigger NICHT. Modul-SET-Änderung braucht (Re-)Load.
- **Trick:** Trigger-BEDINGUNG wird zur Feuer-Zeit (Laufzeit) ausgewertet, NICHT beim Laden. → EIN immer geladenes Dispatcher-Modul A, dessen Trigger live Werte prüfen und je nach Wert andere Aktions-Pfade nehmen → Verhalten on-the-fly umschaltbar OHNE Reload, OHNE Karten anzufassen. Werte-getrieben statt modul-tausch-getrieben.
- Setzt voraus: Reroute-Hook (injiziert Modul A in-memory bei jedem Char beim Laden) + „Karten nie verändern". Struktur (welche Module) = beim (Re-)Load; Verhalten/Pfade = on-the-fly. On-demand-Re-Apply = `KickCard`+`AddCard` (kurzes Flackern).
- **Wert-Kanal ✅ bewiesen in-game 2026-06-27:** `apply_state setCardStorage(seat,key,val)` schreibt genau dorthin, wo Modul-Expression „Get Card Storage Bool/Int" liest. Gegate Confinement (`build_confinement_gated`, Hook v4 injiziert immer) confined 3 Inmates rein flag-getrieben, Karten unangetastet. „Ursache A" geschlossen — kein nativer storeCard-Hack nötig. Char-Werte (virtue/corruption/stats) ebenfalls bewiesen via `apply_state`.

### Reroute-Hook + mwa_id (STATUS-Banner, MEMORY)
- **Reroute-Hook auf `AAUCardData::UpdateModules`** schreibt die Karten-Modul-Liste zur Laufzeit (Confinement via Hook in-game bewiesen). Rename-stabile `mwa_id` als Karten-Global (Round-Trip bewiesen); `memory.db` + API auf mwa_id umgekeyt. Karte liefert Modul-NAMEN, Logik immer aus `data/override/module`-Def. NEXT = Phase 3 (mwa-Flag + clear+replace). Handover: `HANDOVER_reroute_mwaid_2026-06-26.md`.

### Modul-Format / Tooling (STATUS-Banner)
- **Modul-Format geknackt (2026-06-26):** `module_format.py` = vollständiger Codec (decode+encode), byte-genau auf **466/466 Module × 2 Welten = 932 Dateien** verifiziert. Format-Quelle: AAU `Functions/Serialize.h` (generische ReadData/WriteData). ID-Katalog fertig: `MODULE_ID_CATALOG.md` (Events/Actions/Expressions). Builder `module_authoring.py`. Regressionstest `_batch_test.py`. `module_schema.py`/`module_decode.py` = überholte WIP-Vorläufer.
- **`card_edit.py` (Evolution-Editor):** Karten-Element = Definitionsdatei byte-identisch → Splice ohne Trigger-Dekodierung (`aaUd`-Chunk). Roundtrip auf Airi-Kopie (count 9→10, TrAt-Member erhalten, PNG-CRCs valid, Verbatim-Safety-Guard). Offen: In-Game-Effekt-Test + Remove.
- **Modul-Scan:** 466 Module → `module_catalog.json`/`.md`.

### Aktivität / Evolution (§4.7)
- AA2 hat Stat-/Ranking-System: **Strength, Intelligence, Sociability, Stamina** + Virtue. Belege: Club Leader (raise Str/reduce Stamina), Weight Issues (`Weight_-100`…`Weight_100`), Corruption (`corruption1-4`, virtue↓→corrupted style). Depression (3 Stufen), Nine Lives (Style-Wechsel bei „Tod").
- Zwei DB-Ebenen: Zustands-DB (*was IST*) + Aktivitäts-DB (*was GETAN*: training_count, sex_count, fights_won). Aktivitäts-DB = Auslöser via Schwellen-Resolver am End-Day.
- Aktivität zählen: Trigger zählt bei Erfolg in Card Storage hoch, Python liest am End-Day. Buff über MODUL realisieren (z.B. „Martial Arts Prodigy"), nicht rohen Stat schreiben.
- Gebaut school-seitig: `char_activity` + `activity_snapshot.lua` + Ingest (unit-getestet); H/Climax via `m_climaxCount`/`on.end_h`. Maps: `MODULE_CATEGORIZATION.md`, `EVOLUTION_MAP.md`.

### Combo-Hints (§5.2)
| Modul | Combo | Effekt |
|---|---|---|
| Banchou (kiss of death) | insult → kiss | Gang-Mitglied ermordet Ziel |
| Banchou (Gang-Befehl) | get along with X → erneut ansprechen → Force | Mitglied führt Aktion an X aus |
| Banchou (rauswerfen) | insult → Go Away | Mitglied aus Gang werfen |
| Killer | apologize → nevermind | NPC töten (PC Only) |
| Gambler | encourage to study/train/club → get along with their lover | Wett-Mechanik starten |
- Korrektur: „küssen→fight" war FALSCH. Hint-System rein passiv: Modul-Ordner scannen + PC-Card auslesen (AA2QtEdit-Vorlage) + Schnittmenge mit Hand-Dictionary + Lücken-Flag.

### Referenzen / Pfade (§10)
- AAU Repo github.com/aa2g/AA2Unlimited; Wiki; Expressions.cpp/Event.cpp/Module.cpp Quellen. AA2QtEdit github.com/geneishouko/AA2QtEdit. AAU Discord Invite `MqP8rwwSP4`. AA2MiniPPX Torrent-XML tsukiyo.me/AAA/AA2MiniPPX.xml. Card-DB db.bepis.io/aa2.

---

## TEIL 3 — [LATENT] (unbestätigt / offen / TODO / Backlog / Idee / „für später")

- **[LATENT]** §1 — Ob im /aa2g/-Umfeld ein experimenteller EXE-Hack die Seat-Tabelle (25-Cap) aufbohrt. Nicht dokumentiert, sehr unwahrscheinlich; nur via Discord klärbar.
- **[LATENT]** §2.3 / §7-#4 — Weg A „Jail-Button direkt in Spiel-UI injizieren via AAU-Lua": ob auf DEM Heim-Screen platzierbar = unbestätigt (Discord/Quellcode). (Weg B Overlay ist die gewählte Umgehung.)
- **[LATENT]** §2.2 (B) — Hat `aa2play.exe` selbst eine Instanz-Sperre ohne PPeX? (war bisher von PPeX verdeckt) — als Variante-B-Test notiert; faktisch durch Mutex-Fund beantwortet, aber Variante B (PPeX ganz aus, lose Dateibasis) selbst nie real gefahren.
- **[LATENT]** §3.3 — Ob das Teleport-ZIEL einer Phase unabhängig umleitbar ist (vs. nur die Perioden-Nummer). Als „unkritisch" markiert, aber offen.
- **[LATENT]** §3.3 — Verifikation: `CurrentPeriod` an einem Sonntag mitloggen (fährt Sonntag anderes Phasen-Schema?). Indiz für variable Phasen-Sequenz, nicht final geprüft.
- **[LATENT]** §3.1/§7-#3 — Verhalten der versteckten Instanz bei Fokusverlust (pausiert sie wirklich?). Als „egal, Design=1 Welt aktiv" abgetan, aber ungetestet.
- **[LATENT]** §5.2 — TODO später: vollständige Combo-Tabelle aus der ganzen Modulliste extrahieren (~250 Module durchgehen).
- **[LATENT]** §5.4 / §7-#5 — Programmatische Aktions-Auslösung (Klick-zum-Ausführen einer Combo): `geass` erzwingt nur Ergebnis, nicht Auswahl; programmatisches Auslösen unbestätigt. Input-Automation fragil. Optionaler Aufsatz NACH der Anzeige.
- **[LATENT]** §6 — Shadow Sets (`!`-Präfix-Ordner) als toggle-barer Asset-Layer (Alternative zu getrennten Installationen) — notiert, nicht gewählt.
- **[LATENT]** §8 NEXT — Optik pro Welt (eigene Backgrounds/Reskin via Override/Shadow-Set) noch nicht gebaut.
- **[LATENT]** §8 NEXT-3 / §9b — Geteilte Basis via Junctions (63 GB → 21 GB) + Paketierung zu einem Installer.
- **[LATENT]** §8b — Mutex-Closer von externem .NET-Tool nach Python (ctypes) portieren (für self-contained Paket).
- **[LATENT]** §8b — Gepatchten `PPeXM64` self-contained (.NET gebündelt) publishen. Gesamter Installer-Ablauf (AAU finden → Junctions → Lua-Patches → DLL → Module/Assets/Saves → DB → Config) noch nicht gebaut.
- **[LATENT]** §12 — Auto-Save im ~7-Tage-Fenster (falls Spieler NICHT speichert → jail leer): Orchestrator triggert an Tagesgrenze Save der aktiven + Capture der inaktiven Welt → Commit ins Journal. Nächste Iteration, ungebaut.
- **[LATENT]** §2.4d — Optionale Verfalls-/Abkühl-Regel für schlafende Beziehungen während Abwesenheit (X Tage weg → Freundschaft −Y). Freies Design, ungebaut.
- **[LATENT]** §3.1 (Status-Block) — Wochentag extern tracken/setzen (Fr/Sa/So, `GetGameTimeData().day` 0–6), da Phasen-Forcen den Engine-Kalender stört. Separater Baustein, ungebaut.
- **[LATENT/Backlog]** §★-Evolutions-Achsen: 
  - **B1 Rassen-Achse (Race-XP) — nächster konkreter Bau.** 24 Rassen × 5 Valenzen (DESIGNATION innate; BIAS/PREJUDICE/HOSTILE/OBSESSION developable). Eskalation neg: `neutral→PREJUDICE→HOSTILE/hunter→HOSTILE/natenemy→HOSTILE/slayer`; pos: `neutral→BIAS→OBSESSION`. Braucht `chars.race` (extern aus Karten-Modulen an Tagesgrenze gelesen) + Tabelle `char_race_xp(char_id, other_race, positive, negative)`.
  - **B2 Slave-Progression** `unbroken→broken→trained`: KEIN bestehendes Modul → Custom-Modul (3 Stufen, Card-Storage-Flag-gegated, DB-Zähler-getrieben). Kommt mit Status-Schicht.
  - **B3 Lineage/Reinkarnation** „als Nachkomme wieder aufwachen, nicht tötbar": einziges genuin neues Daten-Konzept (Eltern→Kind-Verknüpfung). Invariante: `char_id`/`chars` erweiterbar auf `parent_id`/`lineage_id`. Baustein „nicht tötbar" = `Undying`-Modul (GATE). Nur Invariante wahren, kein Code.
  - **B4 Welt-Features** „Slave Market", „Breed Room" über B2/B3 — weit downstream, nur Intent.
- **[LATENT]** Dispatcher-Kapitel — Konkreter Dispatcher-Modul-Bau (Trigger mit verzweigten Bedingungen via `module_authoring.py`) + Pfad-Kalibrierung noch ausstehend; ganze Evolutions-Schicht (Status, Race-Attitude, Loneliness, Training→Transformation) wert-getrieben einzubauen.
- **[LATENT]** STATUS-Block (offener Test) — Confinement via AA2QtEdit auf 1 jail-Karte installieren, um zu klären ob Module nur „In Use" auf Karte laden (Verdacht warum NPCs free-roamen statt in Zelle).
- **[LATENT]** STATUS — ⬜-Items: Status-Module (Prisoner/Ex/Rehabilitated), Einsamkeits-/Loner-Module aus `social_wealth`, Heimkehrer-Szenario + Offline-Resolver (täglicher Tick), Training→Transformation (chaste→Sex Addict, →Martial Arts Prodigy), Rückkehr-Pfad jail→school, Zustand→Modul-MAP (das „Gehirn", hand-kuratiert), jail-seitiger Aktivitäts-Capture + In-Game-Test, 2c jail-Restore (`restore_rels`, Test offen).

---

## TEIL 4 — [REJECTED] (verworfene Wege + Grund)

- **[REJECTED: kein Lua-Raum-Setter]** Map-Eject / NPC auf einen Knoten halten per reinem Lua. `GetCurrentRoom` nur lesbar; `m_forceAction` Userdata, nicht erreichbar. → stattdessen Trigger-Editor-Modul (`NpcMoveRoom`).
- **[REJECTED: riskant]** `g_poke` auf den `m_forceAction`-Offset für Confinement — CharInstData-Adresse aus Lua nicht zugänglich, Crash-Risiko. → Trigger-Weg gewählt.
- **[REJECTED: zu komplex zum Abwandeln]** Vorhandenes Jailer-Modul (34KB binär) direkt anpassen. → neues Minimal-Modul (`CONFINEMENT_MODULE_SPEC.md`).
- **[REJECTED: Spiel startet ohne PPeX nicht]** Variante B (PPeX ganz aus, lose geteilte Dateibasis via Junction) — kein bUsePPeX-aus-Test möglich beim stark gemoddeten Spiel. → Weg C (PPeX multi-client-Patch) gesetzt.
- **[REJECTED: Engine-Feature existiert nicht]** Annahme „jail rollt zurück wenn älterer school-Save geladen wird" — es gibt pro Playthrough nur EINEN Save-Slot, Speichern überschreibt immer. → DB ist einziger Verlaufs-Speicher.
- **[REJECTED: zu tief/fragil]** Cold-Load per direktem Funktionsaufruf nachbauen — am Hauptmenü Container-Kette leer (Container wird vom Lade-Vorgang selbst erzeugt), Load ist event-/dispatch-getrieben (Queue um Global `0x767f48`). → game-eigener Menü-Load EINMAL beim Boot per UI-Automation (nicht Per-Frame-Automatik).
- **[REJECTED: crasht]** Live-Reload über eine laufende Klasse (`0x10E9C8`, globaler Manager `0xB6264` dangling). → Mid-Session-Save-Swap nur via Kill+Restart.
- **[REJECTED: nicht möglich]** Modul-IN-USE-Liste einer Card zur Laufzeit aus Lua ändern. → vorinstalliertes Modul + Card-Storage-Flag-Gating (bzw. später Reroute-Hook auf `UpdateModules`).
- **[REJECTED: erbt Nebeneffekte]** Weg 1 „vorhandene Module für Status schalten" — Module tun oft mehr als gewünscht, nicht präzise tunebar. → Weg 2 dediziertes Custom-Modul.
- **[REJECTED: User-Erinnerung falsch]** Combo „küssen→fight"; korrekte Banchou/Killer/Gambler-Sequenzen siehe §5.2.
- **[REJECTED: Device-Loss]** Exklusiver DX9-Fullscreen für den Switch (schwarzes Bild beim Verstecken). → Borderless-Windowed Pflicht.
- **[REJECTED: nicht gewollt]** Datenmodell-Variante B (getrennte Leben pro Welt, kein Sync — Char „vergisst" Entwicklung). → Variante A (Selbst-Werte folgen Char, Beziehungen pro Welt lokal).
- **[REJECTED-Annahme korrigiert]** „minimal RAM" für versteckte Instanz — `SW_HIDE` gibt RAM nicht frei; voller Footprint ab Launch. Ebenso „inaktive Welt eingefroren tot" → korrigiert zu täglichem Hintergrund-Tick (§4.8a).

---

## TEIL 5 — Future-World & Scaling Ideen (§9b u.a.)

- **Generisches Welten-System statt „Jail":** Jail = erste Instanz. Weitere Welten (**Beach, Resort, Apartment Complex**) fallen fast gratis raus, WENN Framework von Anfang generisch (Welten als Config, nicht hardcoded).
- **Skaliert gratis:** mehr Welten (N vorkonfigurierte Installs), Optik/Backgrounds pro Welt (Override-Layer), eigene Rosters/NPCs (eigenes Save), gesperrte/freischaltbare Bereiche (Eject-Logik pro Welt), Card-Transfer zwischen ALLEN Welten (parametrisiertes Mover-Script Welt A→B), Switch (Welten-Wähler-Menü statt einzelnem Jail-Button).
- **Skaliert NICHT:** keine echten neuen Map-Layouts (Beach = Schul-Map mit Strand-Texturen, kein echter Strand), keine welt-spezifischen neuen Aktionen. Funktioniert für „dieselbe soziale Sim an anderem Ort"; nicht für fundamental anderes Gameplay.
- **Phasen-Hebel als Welt-Rhythmus:** `on.period`-Set gibt jeder Welt eigenen Tagesrhythmus (Beach: alle Phasen → Strand-Knoten). Hebt „Welt=Reskin" zu „Welt=eigener Ablauf".
- **RAM-adaptive Lade-Strategie:** ~1–1,5 GB/Instanz; 5 Welten vorgeladen ≈ 5–7,5 GB. 32 GB → alle vorladen (Sofort-Switch überall); 16 GB → nur aktive + wahrscheinlichste nächste, Rest on-demand (Kill+Restart). Launcher liest `psutil.virtual_memory()` → adaptiv. Optional User-Setting „Performance- vs. Sofort-Modus".
- **Echte Obergrenze = Einrichtungsaufwand**, nicht RAM. Jede Welt = handgemachte vorkonfigurierte Installation. → Welten-Setup automatisieren/templaten.
- **Installer-Idee (§8b):** EINE Install-Datei, Endnutzer installiert nichts selbst. Python via PyInstaller/Nuitka zu einer `.exe`; gepatchter PPeXM64 self-contained; Mutex-Closer in ctypes. Schritte: AAU finden → Welt-Ordner per Junction → Lua-Patches → gepatchte DLL (Original sichern) → Custom-Module + Assets + Save-Vorlagen → DB → Config + Start-Verknüpfung. Skaliert auf N Welten.
- **Konsequenz für Bau JETZT:** Welten als Config-Einträge (Name, Install-Pfad, Save-Pfad, Override-Set, erlaubte/gesperrte Knoten); Switch-/Transfer-/Reload-Logik parametrisiert über Welt-ID, nicht „school"/"jail" hardcoded; schlanke Abhängigkeiten (nur stdlib/ctypes).
